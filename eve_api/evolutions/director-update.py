from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('EVEPlayerCharacter', 'director_update', models.BooleanField, initial=False)
]

