from django.db import models
from django.contrib.auth.models import User
from eve_api.models.api_player import EVEAccount

class UserProfile(User):
    eveaccount = models.ForeignKey(EVEAccount)

class Site(models.Model):
    url = models.CharField(max_length=200)
    active = models.BooleanField()
    api = models.CharField(max_length=200)

class SiteAccount(models.Model):
    user = models.ForeignKey(UserProfile)
    site = models.ForeignKey(Site)
    username = models.CharField(max_length=200)
    active = models.BooleanField()

