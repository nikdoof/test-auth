from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User, UserManager, Group
from eve_api.models import EVEAccount

from services import get_api

## Exceptions

class CorporateOnlyService(Exception):
    pass

class ExistingUser(Exception):
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

    def update_access(self):
        """ Steps through each Eve API registered to the user and updates their group 
            access accordingly """
        self.user.groups.clear()
        for eacc in EVEAccount.objects.filter(user=self.user):
            for char in eacc.characters.all():
                if char.corporation.group:
                    self.user.groups.add(char.corporation.group)
                

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
    groups = models.ManyToManyField(Group, blank=False)

    @property
    def provide_login(self):
        return self.api_class.settings['provide_login']

    @property
    def api_class(self):
        return get_api(self.api)

    def __str__(self):
        return self.name

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

        api = self.service.api_class()

        if self.active:
            if not api.check_user(self.username):
                api.add_user(self.username, self.password)
            else:
                raise ExistingUser('Username %s has already been took' % self.username)
        else:
            if api.check_user(self.username):
                api.delete_user(self.username)

        # All went OK, save to the DB
        return models.Model.save(self)

    @staticmethod
    def pre_delete_listener( **kwargs ):
        api = kwargs['instance'].service.api_class
        if api.check_user(kwargs['instance'].username):
            api.delete_user(kwargs['instance'].username)

signals.pre_delete.connect(ServiceAccount.pre_delete_listener, sender=ServiceAccount)
