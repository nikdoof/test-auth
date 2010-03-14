import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from eve_api.cron import UpdateAPIs

b = UpdateAPIs()
b.job()

from sso.cron import RemoveInvalidUsers

b = RemoveInvalidUsers()
b.job()
