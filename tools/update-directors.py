#!/usr/bin/env python
"""Executes a Django cronjob"""

import os

# Set niceness
os.nice(20)

# Activate the virtualenv
path = os.path.dirname(os.path.realpath( __file__ ))
activate_this = os.path.join(path, 'env/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

from django.core.management import setup_environ
import settings
setup_environ(settings)

from eve_api.models import EVEPlayerCharacter
from django.contrib.auth.models import Group, User

g = Group.objects.get(name="Alliance Directors")

users = []
for char in EVEPlayerCharacter.objects.filter(corporation__alliance__name="Test Alliance Please Ignore",director=True):
    users.append(char.eveaccount_set.all()[0].user)

add = set(users) - set(g.user_set.all())
rem = set(g.user_set.all()) - set(users)

for m in rem:
    m.groups.remove(g)

for m in add:
    m.groups.add(g)
