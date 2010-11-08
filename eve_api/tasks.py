from celery.decorators import task
from eve_api.api_puller.accounts import import_eve_account
from eve_api.app_defines import *
from sso.tasks import update_user_access

@task()
def import_apikey(api_userid, api_key, user=None, force_cache=False):

    log = import_apikey.get_logger()
    l.info("Importing %s/%s" % (api_userid, api_key))
    acc = import_eve_account(api_key, api_userid, force_cache=force_cache)
    donecorps = []
    if acc and acc.api_status == API_STATUS_OK:
        if user and not acc.user:
            acc.user = user
        if acc.api_keytype == API_KEYTYPE_FULL and acc.characters.filter(director=1).count():
            donecorps = []
            for char in acc.characters.filter(director=1):
                if not char.corporation.id in donecorps:
                    #pull_corp_members(acc.api_key, acc.api_user_id, char.id)
                    char.corporation.query_and_update_corp()
                    donecorps.append(char.corporation.id)

        for char in acc.characters.all():
            try:
                if char.corporation.id not in donecorps:
                    char.corporation.query_and_update_corp()
                    donecorps.append(char.corporation.id)
            except:
                continue

        acc.save()
        if acc.user:
             update_user_access.delay(user=acc.user)

    return acc
