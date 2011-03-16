#!/usr/bin/env python
"""Executes a Django cronjob"""

import os

# Activate the virtualenv
path = os.path.dirname(os.path.realpath( __file__ ))
os.chdir(os.path.join(path, '..'))
print os.path.cwd()
activate_this = os.path.realpath(os.path.join(path, '../env/bin/activate_this.py'))
execfile(activate_this, dict(__file__=activate_this))

import sys
import logging
from django.core.management import setup_environ
import settings

setup_environ(settings)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('ts3remove')

from sso.models import Service, ServiceAccount

srv = Service.objects.get(id=14)
api = srv.api_class

#def send_command(self, command, keys=None, opts=None)

duration = 200
out = {}
offset = 0
x = False
while not x:
    ret = api.conn.send_command('clientdblist', keys={'start': offset, 'duration': 200} )
    for rec in ret:
        if type(rec) == type({}):
            out[rec['keys']['cldbid']] = rec['keys']
    if len(ret) < 25: x = True
    offset = offset + duration
    log.info("Got %s" % offset)

groupcheck = []
for k in out.keys()[200:]:
    ret = api.conn.send_command('custominfo', keys={'cldbid': out[k]['cldbid']})

    keys = {}
    for rec in ret:
        if not type(rec) == type(''):
            keys[rec['keys']['ident']] = rec['keys']['value']

    if 'sso_uid' in keys:
        log.info("Processing %s" % keys['sso_uid'])

        try:
            ServiceAccount.objects.get(service_uid=keys['sso_uid'], service=srv)
        except ServiceAccount.DoesNotExist:
            log.info("Deleting %s" % keys['sso_uid'])
            for client in api.conn.send_command('clientlist'):
                if client['keys']['client_database_id'] == k:
                    print log.info("Kicking from TS3 - %s" % keys['sso_uid'])
                    api.conn.send_command('clientkick', {'clid': client['keys']['clid'], 'reasonid': 5, 'reasonmsg': 'Auth service deleted'})
            ret = api.conn.send_command('clientdbdelete', {'cldbid': k })
            print ret
        except ServiceAccount.MultipleObjectsReturned:
            log.info("Deleting multiple service accounts for %s" % keys['sso_uid'])
            ServiceAccount.objects.filter(service_uid=keys['sso_uid'], service=srv).delete()
            
