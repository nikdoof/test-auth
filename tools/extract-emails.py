#!/usr/bin/env python
"""Executes a Django cronjob"""

import os

# Set niceness
os.nice(20)

# Activate the virtualenv
path = os.path.dirname(os.path.realpath( __file__ ))
activate_this = os.path.join(path, 'env/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

import sys
import logging
from django.core.management import setup_environ
import settings

setup_environ(settings)

from eve_api.models import EVEPlayerCharacter
import unicodedata
import re

chars = set(EVEPlayerCharacter.objects.filter(corporation__alliance__name='Test Alliance Please Ignore'))

#f =open('/home/dreddit/email.txt', 'w')

out = {}

for char in chars:
    if len(char.eveaccount_set.all()) > 0:
        name = unicodedata.normalize('NFKD', char.name).encode('ASCII', 'ignore')
        charname = re.sub('[^a-zA-Z0-9_-]+', '', name)
        if char.eveaccount_set.all()[0].user:
            email =  char.eveaccount_set.all()[0].user.email
            out[charname.lower()] = email


for key in out:
    print("%s\t%s" % (key, out[key]))

#f.close()
