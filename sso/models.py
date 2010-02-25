from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User, UserManager

from services import get_api

## Exceptions

class CorporateOnlyService(Exception):
    pass

## Models

class SSOUser(models.Model):
    """ Extended SSO User Profile options """

    user = models.ForeignKey(User, unique=True, related_name='profile')

    default_service_passwd = models.CharField(max_length=200)
    default_service_username = models.CharField(max_length=200, blank=True)
    
    website = models.CharField(max_length=200, blank=True)
    aim = models.CharField(max_length=64, blank=True)
    msn = models.CharField(max_length=200, blank=True)
    icq = models.CharField(max_length=15, blank=True)
    xmpp = models.CharField(max_length=200, blank=True)

    corp_user = models.BooleanField()

    def __str__(self):
        return self.user.__str__()

    @staticmethod
    def create_user_profile(sender, instance, created, **kwargs):   
        print 'trigger', instance
        if created:   
            profile, created = SSOUser.objects.get_or_create(user=instance) 

signals.post_save.connect(SSOUser.create_user_profile, sender=User)

class Service(models.Model):
    name = models.CharField(max_length=200)
    url = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)
    api = models.CharField(max_length=200)

    def __str__(self):
        return "%s: %s" % (self.name, self.api)

class ServiceAccount(models.Model):
    user = models.ForeignKey(User, blank=False)
    service = models.ForeignKey(Service, blank=False)
    username = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=200, blank=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return "%s: %s (%s)" % (self.service.name, self.user.username, self.username)

    def save(self):
        """ Override default save to setup accounts as needed """

        if not self.username:
            self.username = self.user.username

        api = get_api(self.service.api)

        if api.corp_only:
            if not self.user.get_profile().corp_user:
                raise CorporateOnlyService()

        if self.active:
            if not api.check_user(self.username):
                api.add_user(self.username, self.password)
        else:
            if api.check_user(self.username):
                api.delete_user(self.username)

        if self.user.get_profile().corp_user:
            api.set_corp(self.username)

        # All went OK, save to the DB
        return models.Model.save(self)

    @staticmethod
    def pre_delete_listener( **kwargs ):
        api = get_api(kwargs['instance'].service.api)
        if api.check_user(kwargs['instance'].username):
            api.delete_user(kwargs['instance'].username)

signals.pre_delete.connect(ServiceAccount.pre_delete_listener, sender=ServiceAccount)
