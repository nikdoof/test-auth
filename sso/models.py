import re
import unicodedata
import logging
import types

from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User, UserManager, Group
from django.utils import simplejson as json

from jsonfield.fields import JSONField
from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerAlliance, EVEPlayerCharacter
from reddit.models import RedditAccount

from services import get_api

## Exceptions

class CorporateOnlyService(Exception):
    pass

class ExistingUser(Exception):
    pass

class ServiceError(Exception):
    pass

## Models

class SSOUser(models.Model):
    """ Extended SSO User Profile options """

    user = models.ForeignKey(User, unique=True, related_name='profile')

    api_service_password = models.CharField("API Services Password", max_length=200, blank=True)

    def __unicode__(self):
        return self.user.__unicode__()

    @staticmethod
    def create_user_profile(sender, instance, created, **kwargs):   
        if created:   
            profile, created = SSOUser.objects.get_or_create(user=instance) 

signals.post_save.connect(SSOUser.create_user_profile, sender=User)

class SSOUserNote(models.Model):
    """ Notes bound to a user's account. Used to store information regarding the user """

    user = models.ForeignKey(User, blank=False, null=False, related_name='notes')
    note = models.TextField("Note", blank=False, null=False)
    created_by = models.ForeignKey(User, blank=False, null=False)
    date_created = models.DateTimeField(auto_now_add=True, blank=False, null=False,
                                            verbose_name="Date/Time the note was added",
                                            help_text="Shows the date and time the note was added to the account")

    class Meta:
        verbose_name = 'User Note'
        verbose_name_plural = 'User Notes'
        ordering = ['date_created']


class Service(models.Model):
    """
    Service model represents a service available to users, either a website or
    a connection service like Jabber or IRC.
    """

    name = models.CharField("Service Name", max_length=200)
    url = models.CharField("Service URL", max_length=200, blank=True)
    active = models.BooleanField(default=True)
    api = models.CharField("API", max_length=200)
    groups = models.ManyToManyField(Group, blank=True)
    settings_json = JSONField("Service Settings", blank=True, default={})

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['id']

    @property
    def provide_login(self):
        return self.settings['provide_login']

    @property
    def api_class(self):
        api = get_api(self.api)
        api.settings = self.settings
        return api

    def __unicode__(self):
        return self.name

    def save(self):
        if not self.settings_json or self.settings_json == {}:
            if self.api:
                self.settings_json = self.settings
            else:
                self.settings_json = {}
        else:
            if isinstance(self.settings_json, types.StringTypes):
                self.settings_json = eval(self.settings_json)

        return models.Model.save(self)

    @property
    def settings(self):

        if self.settings_json:
            setdict = self.settings_json
        else:
            setdict = {}

        # Load defaults from the module's settings dict
        if self.api:
            modset = get_api(self.api).settings
            for k in modset:
                if not k in setdict:
                    setdict[k] = modset[k]

        return setdict


class ServiceAccount(models.Model):
    """
    ServiceAccount represents the user's account on a Service.
    """
    user = models.ForeignKey(User, blank=False)
    service = models.ForeignKey(Service, blank=False)
    service_uid = models.CharField("Service UID", max_length=200, blank=False)
    active = models.BooleanField(default=True)

    character = models.ForeignKey(EVEPlayerCharacter, null=True)
    username = None
    password = None

    class Meta:
        verbose_name = 'Service Account'
        verbose_name_plural = 'Service Accounts'
        ordering = ['user']

    def __unicode__(self):
        return u"%s: %s (%s)" % (self.service.name, self.user.username, self.service_uid)

    def save(self):
        if self.id:
            org = ServiceAccount.objects.get(id=self.pk)

            if org.active != self.active and self.service_uid:
                if self.active:
                    self.service.api_class.enable_user(self.service_uid, '')
                else:
                    self.service.api_class.disable_user(self.service_uid)

        models.Model.save(self)

    @staticmethod
    def pre_delete_listener( **kwargs ):
        if not kwargs['instance'].service.api_class.delete_user(kwargs['instance'].service_uid):
            raise ServiceError('Unable to delete account on related service')

signals.pre_delete.connect(ServiceAccount.pre_delete_listener, sender=ServiceAccount)
