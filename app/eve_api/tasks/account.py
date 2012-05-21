import sys
from datetime import datetime, timedelta
from xml.dom import minidom
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import now, utc

from celery.task import task
from celery.task.sets import TaskSet
from gargoyle import gargoyle

from eve_proxy.exceptions import *
from eve_proxy.models import CachedDocument
from eve_api.models import EVEAccount, EVEPlayerCharacter
from eve_api.app_defines import *
from eve_api.api_exceptions import *
from eve_api.utils import basic_xml_parse_doc
from eve_api.tasks.character import import_eve_characters
from eve_api.tasks.corporation import import_corp_members, import_corp_details
from sso.tasks import update_user_access


@task(ignore_result=True, expires=120)
def queue_apikey_updates(update_delay=86400, batch_size=50):
    """
    Updates all Eve API elements in the database
    """

    log = queue_apikey_updates.get_logger()

    if gargoyle.is_active('api-disableprocessing'):
        log.info("Backend processing disabled, exiting")
        return

    # Update all the eve accounts and related corps
    delta = timedelta(seconds=update_delay)
    log.info("Updating APIs older than %s" % (now() - delta))

    if gargoyle.is_active('eve-cak'):
        accounts = EVEAccount.objects.filter(api_last_updated__lt=(now() - delta)).exclude(api_status__in=[API_STATUS_ACC_EXPIRED, API_STATUS_KEY_EXPIRED, API_STATUS_AUTH_ERROR]).order_by('api_last_updated')[:batch_size]
    else:
        accounts = EVEAccount.objects.filter(api_last_updated__lt=(now() - delta)).exclude(api_status__in=[API_STATUS_ACC_EXPIRED, API_STATUS_KEY_EXPIRED, API_STATUS_AUTH_ERROR]).exclude(api_keytype__gt=2).order_by('api_last_updated')[:batch_size]
    log.info("%s account(s) to update" % accounts.count())
    for acc in accounts:
        log.debug("Queueing UserID %s for update" % acc.pk)
        if not acc.user:
            acc.delete()
            continue
        import_apikey.delay(api_key=acc.api_key, api_userid=acc.pk)


@task(ignore_result=True)
def import_apikey(api_userid, api_key, user=None, force_cache=False, **kwargs):
    """
    Imports a EVE Account from the API, doesn't return a result
    """
    log = import_apikey.get_logger()
    try:
        import_apikey_func(api_userid, api_key, user, force_cache, log)
    except (APIAccessException, DocumentRetrievalError), exc:
        log.error('Error importing API Key - flagging for retry', exc_info=sys.exc_info(), extra={'data': {'api_userid': api_userid, 'api_key': api_key}})
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
        log.error('Error importing API Key - flagging for retry', exc_info=sys.exc_info(), extra={'data': {'api_userid': api_userid, 'api_key': api_key}})
        import_apikey_result.retry(args=[api_userid, api_key, user, force_cache, callback], exc=exc, kwargs=kwargs)
    else:
        if callback:
            subtask(callback).delay(account=results)
        else:
            return results


def import_apikey_func(api_userid, api_key, user=None, force_cache=False, log=logging.getLogger(__name__)):
    log.info('Importing %s/%s' % (api_userid, api_key))

    try:
        account = EVEAccount.objects.get(pk=api_userid)
    except EVEAccount.DoesNotExist:
        account = None

    # Use CAK if enabled and either a new key or flagged as so
    if (gargoyle.is_active('eve-cak') and (not account or account.is_cak)):
        auth_params = {'keyid': api_userid, 'vcode': api_key}
        keycheck = CachedDocument.objects.api_query('/account/APIKeyInfo.xml.aspx', params=auth_params, no_cache=True)
        doc = basic_xml_parse_doc(keycheck)['eveapi']

        if not 'error' in doc:
            if not account:
                account, created = EVEAccount.objects.get_or_create(pk=api_userid)
                if user:
                    account.user = User.objects.get(id=user)
            if not account.api_key == api_key:
                account.api_key = api_key

            keydoc = doc['result']['key']
            if keydoc['type'] == 'Character':
                account.api_keytype = API_KEYTYPE_CHARACTER
            elif keydoc['type'] == 'Corporation':
                account.api_keytype = API_KEYTYPE_CORPORATION
            elif keydoc['type'] == 'Account':
                account.api_keytype = API_KEYTYPE_ACCOUNT
            account.api_accessmask = int(keydoc['accessMask'])
            if not keydoc['expires'] == '':
                account.api_expiry = datetime.strptime(keydoc['expires'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=utc)

            # Checks account status to see if the account is still active
            if not account.api_keytype == API_KEYTYPE_CORPORATION:

                if account.has_access(25):
                    status = CachedDocument.objects.api_query('/account/AccountStatus.xml.aspx', params=auth_params, no_cache=True)
                    status = basic_xml_parse_doc(status)['eveapi']
                    if not status.get('error', None):
                        paiddate = datetime.strptime(status['result']['paidUntil'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=utc)
                        if paiddate <= now():
                            account.api_status = API_STATUS_ACC_EXPIRED
                        else:
                            account.api_status = API_STATUS_OK
                else:
                    account.api_status = API_STATUS_INVALID_PERMISSIONS

                if not account.check_access(getattr(settings, 'EVE_API_MINIMUM_KEYMASK', 59638024)):
                    account.api_status = API_STATUS_INVALID_PERMISSIONS
            else:
                # If its a corp key, and we've not errored so far, assume is OK.
                account.api_status = API_STATUS_OK

            # Remove deleted or traded characters
            newcharlist = [int(char['characterID']) for char in doc['result']['key']['characters']]
            for char in account.characters.all().exclude(id__in=newcharlist):
                account.characters.remove(char)

            # Schedule a task to update the characters
            if account.user:
                cb = update_user_access.subtask(kwargs={'user': account.user.id })
            else:
                cb = None
            import_eve_characters.delay(newcharlist, key_id=account.pk, callback=cb)

        else:
            # No account object, just return
            if not account:
                return

            if not account.api_key == api_key:
                # Attempted change of key failed, ignore
                return

            error = doc['error']['code']
            if int(error) >= 500:
                # API disabled, down or rejecting, return without changes
                return
            elif error in ['202', '203', '204', '205', '212']:
                account.api_status = API_STATUS_AUTH_ERROR
            elif error == '211':
                account.api_status = API_STATUS_ACC_EXPIRED
            elif error in ['222', '223']:
                account.api_status = API_STATUS_KEY_EXPIRED
            elif error in ['221']:
                account.api_status = API_STATUS_INVALID_PERMISSIONS
            else:
                account.api_status = API_STATUS_OTHER_ERROR

            if account.user:
                update_user_access.delay(account.user.id)

    else:
        auth_params = {'userid': api_userid, 'apikey': api_key}
        account_doc = CachedDocument.objects.api_query('/account/Characters.xml.aspx', params=auth_params, no_cache=force_cache)
        doc = basic_xml_parse_doc(account_doc)['eveapi']

        if not 'error' in doc:
            if not account:
                account, created = EVEAccount.objects.get_or_create(pk=api_userid)
            if user and not account.user:
                account.user = User.objects.get(id=user)
            if not account.api_key == api_key:
                account.api_key = api_key
            account.api_status = API_STATUS_OK

            if not account.api_keytype or account.api_keytype == API_KEYTYPE_UNKNOWN:
                keycheck = CachedDocument.objects.api_query('/account/AccountStatus.xml.aspx', params=auth_params, no_cache=True)
                keydoc = basic_xml_parse_doc(keycheck)['eveapi']
                if 'error' in keydoc:
                    account.api_keytype = API_KEYTYPE_LIMITED
                elif not 'error' in keydoc:
                    account.api_keytype = API_KEYTYPE_FULL
                else:
                    account.api_keytype = API_KEYTYPE_UNKNOWN

            # Remove deleted or traded characters
            newcharlist = [int(char['characterID']) for char in doc['result']['characters']]
            for char in account.characters.all().exclude(id__in=newcharlist):
                account.characters.remove(char)

            # Schedule a task to update the characters
            if account.user:
                cb = update_user_access.subtask(kwargs={'user': account.user.id })
            else:
                cb = None
            import_eve_characters.delay(newcharlist, key_id=account.pk, callback=cb)

        else:
            # No account object, just return
            if not account:
                return

            if not account.api_key == api_key:
                # Attempted change of key failed, ignore
                return

            error = doc['error']['code']
            if int(error) >= 500:
                # API disabled, down or rejecting, return without changes
                return
            elif error in ['202', '203', '204', '205', '212']:
                account.api_status = API_STATUS_AUTH_ERROR
            elif error in ['211', '223']:
                account.api_status = API_STATUS_ACC_EXPIRED
            else:
                account.api_status = API_STATUS_OTHER_ERROR

            if account.user:
                update_user_access.delay(account.user.id)

    account.api_last_updated = now()
    account.save()
    return account

