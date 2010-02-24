from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    url = models.CharField(max_length=200)
    active = models.BooleanField()
    api = models.CharField(max_length=200)

class ServiceAccount(models.Model):
    user = models.ForeignKey(User)
    service = models.ForeignKey(Service)
    username = models.CharField(max_length=200)
    active = models.BooleanField()

