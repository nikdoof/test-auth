from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('EVEPlayerCharacter', 'applications', models.BooleanField, initial=False)
]

