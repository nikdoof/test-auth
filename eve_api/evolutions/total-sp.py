from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('EVEPlayerCharacter', 'total_sp', models.IntegerField, initial=0)
]

