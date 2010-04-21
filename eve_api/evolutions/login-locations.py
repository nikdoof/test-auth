from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('EVEPlayerCharacter', 'current_location_id', models.IntegerField, null=True),
    AddField('EVEPlayerCharacter', 'last_login', models.DateTimeField, null=True),
    AddField('EVEPlayerCharacter', 'last_logoff', models.DateTimeField, null=True)
]

