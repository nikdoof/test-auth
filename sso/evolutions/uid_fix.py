from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('ServiceAccount', 'service_uid', models.CharField,  max_length=200, blank=False)
]
