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
from django.contrib.auth.models import Group
import unicodedata
import re

g = Group.objects.get(name="Alliance Directors")
c = EVEPlayerCharacter.objects.filter(corporation__alliance__name="Test Alliance Please Ignore",director=True)

for m in g.user_set.all():
    m.groups.remove(g)

for char in c:
    char.eveaccount_set.all()[0].user.groups.add(g)
