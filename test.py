import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from sso.services.jabber import JabberService

b = JabberService()

print b.check_user('matalok')
