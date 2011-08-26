from datetime import datetime, timedelta
from xml.dom import minidom
import logging

from celery.decorators import task
from celery.task.sets import TaskSet

from eve_proxy.exceptions import *
from eve_proxy.models import CachedDocument

from eve_api.models import EVEAccount, EVEPlayerCharacter
from eve_api.app_defines import *
from eve_api.api_exceptions import *
from eve_api.utils import basic_xml_parse_doc
from eve_api.tasks.character import import_eve_characters
from eve_api.tasks.corporation import import_corp_members, import_corp_details

from sso.tasks import update_user_access

from django.contrib.auth.models import User

@task(ignore_result=True, expires=120)
def queue_apikey_updates(update_delay=86400, batch_size=50):
    """
    Updates all Eve API elements in the database
    """

    log = queue_apikey_updates.get_logger()
    # Update all the eve accounts and related corps
    delta = timedelta(seconds=update_delay)
    log.info("Updating APIs older than %s" % (datetime.now() - delta))

    accounts = EVEAccount.objects.filter(api_last_updated__lt=(datetime.now() - delta)).exclude(api_status=API_STATUS_ACC_EXPIRED).exclude(api_status=API_STATUS_AUTH_ERROR).order_by('api_last_updated')[:batch_size]
    log.info("%s account(s) to update" % accounts.count())
    for acc in accounts:
        log.debug("Queueing UserID %s for update" % acc.api_user_id)
        if not acc.user:
            acc.delete()
            continue
        import_apikey.delay(api_key=acc.api_key, api_userid=acc.api_user_id)


@task(ignore_result=True)
def import_apikey(api_userid, api_key, user=None, force_cache=False, **kwargs):
    """
    Imports a EVE Account from the API, doesn't return a result
    """
    log = import_apikey.get_logger()
    try:
        import_apikey_func(api_userid, api_key, user, force_cache, log)
    except (APIAccessException, DocumentRetrievalError), exc:
        log.error('Error importing API Key - flagging for retry')
        import_apikey.retry(args=[api_userid, api_key, user, force_cache], exc=exc, kwargs=kwargs)


@task()
def import_apikey_result(api_userid, api_key, user=None, force_cache=False, callback=None, **kwargs):
    """
    Imports a EVE Account from the API and returns the account object when completed
    """

    log = import_apikey_result.get_logger()
    try:
        results = import_apikey_func(api_userid, api_key, user, force_cache, log)
    except (APIAccessException, DocumentRetrievalError), exc:
        log.error('Error importing API Key - flagging for retry')
        import_apikey_result.retry(args=[api_userid, api_key, user, force_cache, callback], exc=exc, kwargs=kwargs)
    else:
        if callback:
            subtask(callback).delay(account=results)
        else:
            return results


def import_apikey_func(api_userid, api_key, user=None, force_cache=False, log=logging.getLogger(__name__)):
    log.info('Importing %s/%s' % (api_userid, api_key))

    auth_params = {'userid': api_userid, 'apikey': api_key}
    account_doc = CachedDocument.objects.api_query('/account/Characters.xml.aspx', params=auth_params, no_cache=force_cache)

    doc = basic_xml_parse_doc(account_doc)['eveapi']

    # Checks for a document error
    if 'error' in doc:
        try:
            account = EVEAccount.objects.get(api_user_id=api_userid)
        except EVEAccount.DoesNotExist:
            # If no Account exists in the DB, just ignore it
            return

        error = doc['error']['code']
        if int(error) >= 500:
            # API disabled, down or rejecting, return without changes
            return
        elif error in ['202', '203', '204', '205', '212']:
            account.api_status = API_STATUS_AUTH_ERROR
        elif error == '211':
            account.api_status = API_STATUS_ACC_EXPIRED
        else:
            account.api_status = API_STATUS_OTHER_ERROR
        account.api_last_updated = datetime.utcnow()
        account.save()
        if account.user:
            update_user_access.delay(account.user.id)
        return account

    # Create or retrieve the account last to make sure everything
    # before here is good to go.
    account, created = EVEAccount.objects.get_or_create(api_user_id=api_userid)
    if not account.api_key == api_key:
        account.api_key = api_key
        account.api_keytype = API_KEYTYPE_UNKNOWN
    account.api_status = API_STATUS_OK
    if user and created:
        account.user = User.objects.get(id=user)

    account.api_last_updated = datetime.utcnow()
    account.save()

    # Check API keytype if we have a character and a unknown key status
    if account.api_keytype == API_KEYTYPE_UNKNOWN:
        keycheck = CachedDocument.objects.api_query('/account/AccountStatus.xml.aspx', params=auth_params, no_cache=True)
        keydoc = basic_xml_parse_doc(keycheck)['eveapi']

        if 'error' in keydoc:
            account.api_keytype = API_KEYTYPE_LIMITED
        elif not 'error' in keydoc:
            account.api_keytype = API_KEYTYPE_FULL
        else:
            account.api_keytype = API_KEYTYPE_UNKNOWN

        account.api_last_updated = datetime.utcnow()
        account.save()

    tasklist = []

    # Process the account's character list
    charlist = set(account.characters.all().values_list('id', flat=True))
    newcharlist = [int(char['characterID']) for char in doc['result']['characters']]

    log.info("[CHAR] Current %s, New: %s, Remove: %s" % (charlist, newcharlist, set(charlist - set(newcharlist))))

    for char in account.characters.filter(id__in=set(charlist - set(newcharlist))):
        account.characters.remove(char)

    if account.user:
        cb = update_user_access.subtask(kwargs={'user': account.user.id })
    else:
        cb = None
    import_eve_characters.delay(newcharlist, api_key, api_userid, callback=cb)

    return account
