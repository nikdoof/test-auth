from datetime import datetime, timedelta
from xml.dom import minidom

from celery.decorators import task

from eve_proxy.models import CachedDocument

from eve_api.models import EVEAccount
from eve_api.app_defines import *
from eve_api.utils import basic_xml_parse

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
def import_apikey(api_userid, api_key, user=None, force_cache=False):
    """
    Imports a EVE Account from the API, doesn't return a result
    """
    import_apikey_func(api_userid, api_key, user, force_cache)

@task()
def import_apikey_result(api_userid, api_key, user=None, force_cache=False):
    """
    Imports a EVE Account from the API and returns the account object when completed
    """
    return import_apikey_func(api_userid, api_key, user, force_cache)

def import_apikey_func(api_userid, api_key, user=None, force_cache=False):
    log = import_apikey.get_logger('import_apikey_result')
    log.info('Importing %s/%s' % (api_userid, api_key))

    auth_params = {'userid': api_userid, 'apikey': api_key}
    account_doc = CachedDocument.objects.api_query('/account/Characters.xml.aspx', params=auth_params, no_cache=force_cache)

    if account_doc and account_doc.body:
        dom = minidom.parseString(account_doc.body.encode('utf-8'))
    else:
        return

    # Checks for a document error
    enode = dom.getElementsByTagName('error')
    if enode:
        try:
            account = EVEAccount.objects.get(id=api_userid)
        except EVEAccount.DoesNotExist:
            # If no Account exists in the DB, just ignore it
            return

        error = enode[0].getAttribute('code')
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
        return account

    # Create or retrieve the account last to make sure everything
    # before here is good to go.
    account, created = EVEAccount.objects.get_or_create(id=api_userid, api_user_id=api_userid, api_key=api_key)
    account.api_status = API_STATUS_OK
    if user and created:
        account.user = user
    account.save()

    account.characters.clear()
    for node in dom.getElementsByTagName('rowset')[0].childNodes:
         try:
             char = import_eve_character.delay(node.getAttribute('characterID'), api_key, api_userid).get()
             account.characters.add(char)
         except AttributeError:
             continue

    # Check API keytype if we have a character and a unknown key status
    if account.api_keytype == API_KEYTYPE_UNKNOWN and len(account.characters.all()):
        auth_params['characterID'] = account.characters.all()[0].id
        keycheck = CachedDocument.objects.api_query('/char/AccountBalance.xml.aspx', params=auth_params, no_cache=True)

        if keycheck:
            dom = minidom.parseString(keycheck.body.encode('utf-8'))
            enode = dom.getElementsByTagName('error')

            if enode and int(enode[0].getAttribute('code')) == 200:
                account.api_keytype = API_KEYTYPE_LIMITED
            elif not enode:
                account.api_keytype = API_KEYTYPE_FULL
            else:
                account.api_keytype = API_KEYTYPE_UNKNOWN
        else:
            account.api_keytype = API_KEYTYPE_UNKNOWN

    account.api_last_updated = datetime.utcnow()
    account.save()
    log.debug('Completed')

    donecorps = []
    if account.api_keytype == API_KEYTYPE_FULL and account.characters.filter(director=1).count():
        donecorps = []
        for char in account.characters.filter(director=1):
            if not char.corporation.id in donecorps:
                import_corp_members.delay(api_key=account.api_key, api_userid=account.api_user_id, character_id=char.id)
                donecorps.append(char.corporation.id)

    for id in set(account.characters.all().values_list('corporation__id', flat=True)):
        import_corp_details.delay(corp_id=id)

    account.save()
    if account.user:
         update_user_access.delay(user=account.user.id)

    return account
