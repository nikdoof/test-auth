from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('EVEPlayerCorporation', 'applications', models.BooleanField, initial=False)
]

