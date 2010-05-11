#----- Evolution for sso
from django_evolution.mutations import *
from django.db import models
from django_jsonfield.fields import JSONField

MUTATIONS = [
    AddField('Service', 'settings_json', JSONField, initial='{}'),
]
#----------------------

