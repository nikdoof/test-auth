from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('EVEPlayerAlliance', 'group', models.ForeignKey, null=True, related_model='auth.Group')
]

