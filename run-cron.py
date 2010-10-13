#!/usr/bin/env python
"""Executes a Django cronjob"""

import os

# Activate the virtualenv
path = os.path.dirname(os.path.realpath( __file__ ))
os.chdir(path)
activate_this = os.path.join(path, 'env/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

import sys
import logging
from django.core.management import setup_environ
import settings

setup_environ(settings)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('runcron')

try:
    mod = __import__(sys.argv[1])
except ImportError:
    raise Exception('Error creating service')

for i in sys.argv[1].split(".")[1:]:
    mod = getattr(mod, i)
cron_class = getattr(mod, sys.argv[2])()

log.info("Starting Job %s in %s" % (sys.argv[2], sys.argv[1]))

try:
    cron_class.job()
except KeyboardInterrupt:
    log.error("aborting.")

log.info("Job complete")
