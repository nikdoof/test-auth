#!/usr/bin/env python
"""Executes a Django cronjob"""

PACS = 29

import os, sys

# Set niceness
os.nice(20)

# Activate the virtualenv
path = os.path.dirname(os.path.realpath( __file__ ))
os.chdir(path)
activate_this = os.path.join(path, 'env/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

from django.core.management import setup_environ
import settings
setup_environ(settings)

from eve_api.models import EVEPlayerCharacter
from django.contrib.auth.models import Group, User

from sso.tasks import update_user_access

g = Group.objects.get(name="Alliance Directors")

users = []
for char in EVEPlayerCharacter.objects.filter(corporation__alliance__name="Test Alliance Please Ignore",director=True):
    if char.eveaccount_set.count() and char.eveaccount_set.all()[0].user and not (char.corporation.group and char.corporation.group.id == PACS):
        users.append(char.eveaccount_set.all()[0].user)

add = set(users) - set(g.user_set.all())
rem = set(g.user_set.all()) - set(users)

print "Add:", add
print "Rem:", rem


for m in rem:
    m.groups.remove(g)
    update_user_access.delay(m.id)

for m in add:
    m.groups.add(g)
    update_user_access.delay(m.id)

#for u in set(users):
#    print "Updating %s" % u
#    update_user_access.delay(u.id)
