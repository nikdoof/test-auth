from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('Mumble', 'display', models.CharField, initial='', max_length=200),
    AddField('Mumble', 'server', models.ForeignKey, initial='<<USER VALUE REQUIRED>>', related_model='mumble.MumbleServer'),
    DeleteField('Mumble', 'dbus'),
    ChangeField('Mumble', 'port', initial=None, null=True)
]

