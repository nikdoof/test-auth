import re
import unicodedata
import logging
import types

from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User, UserManager, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils import simplejson as json

from jsonfield.fields import JSONField
from IPy import IP
import dns.resolver

from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerAlliance, EVEPlayerCharacter

from sso.app_defines import *
from sso.services import get_api

## Exceptions


class CorporateOnlyService(Exception):
    pass


class ExistingUser(Exception):
    pass


class ServiceError(Exception):
    pass


class SSOUser(models.Model):
    """ Extended SSO User Profile options """

    user = models.ForeignKey(User, unique=True, related_name='profile')

    primary_character = models.ForeignKey(EVEPlayerCharacter, null=True)
    tag_reddit_accounts = models.BooleanField("Tag Reddit Accounts?", default=False)
    api_service_password = models.CharField("API Services Password", max_length=200, blank=True)

    def __unicode__(self):
        return self.user.__unicode__()

    @staticmethod
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            profile, created = SSOUser.objects.get_or_create(user=instance)

    class Meta:
        permissions = (
            ("can_view_users", "Can view any user's profile"),
            ("can_view_users_restricted", "Can view a restricted user profile"),
            ("can_search_users", "Can use the user search function"),
            ("can_refresh_users", "Can refresh a user's access"),
        )


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


class SSOUserIPAddress(models.Model):
    """
    Stores User Related IP Addresses
    """
    first_seen =  models.DateTimeField(auto_now_add=True, blank=False, null=False,
                                           verbose_name="First sighting date/time",
                                           help_text="Shows the first the user was seen at this IP.")
    last_seen = models.DateTimeField(auto_now_add=True, blank=False, null=False,
                                           verbose_name="First sighting date/time",
                                           help_text="Shows the most recent time the user has been seen at this IP.")
    ip_address = models.CharField("IP Address", max_length=200, blank=False)
    user = models.ForeignKey(User, blank=False, null=False, related_name='ip_addresses')

    @property
    def hostname(self):
        arpa = IP(self.ip_address).reverseName()
        try:
            res = dns.resolver.query(arpa, 'PTR').response
            return res.answer[0][0].to_text()
        except:
            return arpa

    @property
    def related_users(self):
        return SSOUserIPAddress.objects.filter(ip_address=self.ip_address).count()

    def __unicode__(self):
        return self.ip_address

    class Meta:
        verbose_name = 'User IP Addresse'
        verbose_name_plural = 'User IP Addresses'
        ordering = ['user']


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
    def pre_delete_listener(**kwargs):
        if not kwargs['instance'].service.api_class.delete_user(kwargs['instance'].service_uid):
            raise ServiceError('Unable to delete account on related service')

signals.pre_delete.connect(ServiceAccount.pre_delete_listener, sender=ServiceAccount)


class PermissionRuleset(models.Model):
    """ A group of rules to assign a Group to a user """

    name = models.CharField("Name", max_length=200, help_text="Name of the ruleset")
    active = models.BooleanField("Active", help_text="Indicates if the rule will be used during permissions processing")
    group = models.ForeignKey(Group, help_text="Group that will be added to the user's profile if they match the listed rules")

    check_type = models.BooleanField()

    def check_ruleset(self, user):
        if self.check_type == CHECK_TYPE_AND:
            ret = False
            for rule in self.rules:
                ret = rule.check_rule(user)
            return ret
        elif self.check_type == CHECK_TYPE_OR:
            for rule in self.rules:
                if rule.check_rule(user) == True:
                    return True
        return False

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'Ruleset'
        verbose_name_plural = u'Rulesets'


class PermissionRule(models.Model):
    ruleset = models.ForeignKey(PermissionRuleset, related_name='rules')

    obj_type = models.ForeignKey(ContentType, verbose_name="Object Type", help_text="Type of object you want to check for")
    obj_id = models.IntegerField("Object ID")
    related_obj = generic.GenericForeignKey(obj_type, obj_id)

    check_type = models.IntegerField("Check Type")

    def check_rule(self, user):

        if self.obj_type.app_label == 'eve_api' and self.obj_type.model == 'eveplayercorporation':
            return EVEPlayerCharacter.objects.filter(eveaccount__user=user, corporation=self.related_obj).count()
        elif self.obj_type.app_label == 'eve_api' and self.obj_type.model == 'eveplayeralliance':
            return EVEPlayerCharacter.objects.filter(eveaccount__user=user, corporation__alliance=self.related_obj).count()

        return False

    def __unicode__(self):
        #return self.related_obj
        return "%s %s-%s" % (self.ruleset.name, self.obj_type, self.obj_id)

    class Meta:
        verbose_name = u'Rule'
        verbose_name_plural = u'Rules'
