from celery.decorators import task
from eve_api.models import EVEAccount, EVEPlayerCorporation
from eve_api.api_puller.accounts import import_eve_account
from eve_api.api_puller.corp_management import pull_corp_members
from eve_api.app_defines import *
from sso.tasks import update_user_access

@task(ignore_result=True)
def queue_apikey_updates(update_delay=86400, batch_size=50):
    """
    Updates all Eve API elements in the database
    """

    log = queue_apikey_updates.get_logger()
    # Update all the eve accounts and related corps
    delta = datetime.timedelta(seconds=update_delay)
    log.info("Updating APIs older than %s" % (datetime.datetime.now() - delta))

    accounts = EVEAccount.objects.filter(api_last_updated__lt=(datetime.datetime.now() - delta)).exclude(api_status=API_STATUS_ACC_EXPIRED).exclude(api_status=API_STATUS_AUTH_ERROR).order_by('api_last_updated')[:batch_size]
    log.info("%s account(s) to update" % accounts.count())
    for acc in accounts:
        log.debug("Queueing UserID %s for update" % acc.api_user_id)
        if not acc.user:
            acc.delete()
            continue
        import_apikey.delay(api_key=acc.api_key, api_userid=acc.api_user_id)


@task()
def import_apikey(api_userid, api_key, user=None, force_cache=False):
    acc = import_eve_account(api_key, api_userid, force_cache=force_cache)
    donecorps = []
    if acc and acc.api_status == API_STATUS_OK:
        if user and not acc.user:
            acc.user = user
        if acc.api_keytype == API_KEYTYPE_FULL and acc.characters.filter(director=1).count():
            donecorps = []
            for char in acc.characters.filter(director=1):
                if not char.corporation.id in donecorps:
                    import_corp_members.delay(api_key=acc.api_key, api_userid=acc.api_user_id, character_id=char.id)
                    import_corp_details.delay(corp_id=char.corporation.id)
                    donecorps.append(char.corporation.id)

        for char in acc.characters.all():
            try:
                if char.corporation.id not in donecorps:
                    import_corp_details.delay(corp_id=char.corporation.id)
                    donecorps.append(char.corporation.id)
            except:
                continue

        acc.save()
        if acc.user:
             update_user_access.delay(user=acc.user)

    return acc


@task(ignore_result=True)
def import_corp_members(api_userid, api_key, character_id):
    pull_corp_members(api_key, api_userid, character_id)


@task(ignore_result=True)
def import_corp_details(corp_id):
    corp = EVEPlayerCorporation.objects.get_or_create(id=corp_id)
    corp.query_and_update_corp()
    corp.save()
