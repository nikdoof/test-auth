import re
import unicodedata
import logging
import types

from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User, UserManager, Group
from django.utils import simplejson as json

from jsonfield.fields import JSONField
from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerAlliance
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

    default_service_passwd = models.CharField("Default Service Password", max_length=200, blank=True)
    default_service_username = models.CharField("Default Service Username", max_length=200, blank=True)
    
    website = models.CharField("Website URL", max_length=200, blank=True)
    aim = models.CharField("AIM", max_length=64, blank=True)
    msn = models.CharField("MSN", max_length=200, blank=True)
    icq = models.CharField("ICQ", max_length=15, blank=True)
    xmpp = models.CharField("XMPP", max_length=200, blank=True)

    @property
    def _log(self):
        if not hasattr(self, '__log'):
            self.__log = logging.getLogger(self.__class__.__name__)
        return self.__log

    def update_access(self):
        """ Steps through each Eve API registered to the user and updates their group 
            access accordingly """

        self._log.debug("Update - User %s" % self.user)
        # Create a list of all Corp and Alliance groups
        corpgroups = []
        for corp in EVEPlayerCorporation.objects.filter(group__isnull=False):
            if corp.group:
                corpgroups.append(corp.group)  
        for alliance in EVEPlayerAlliance.objects.filter(group__isnull=False):
            if alliance.group:
                corpgroups.append(alliance.group)  
        
        # Create a list of Char groups
        chargroups = []
        for eacc in EVEAccount.objects.filter(user=self.user):
            if eacc.api_status in [1,3]:
                for char in eacc.characters.all():
                    if char.corporation.group:
                        chargroups.append(char.corporation.group)
                    if char.corporation.alliance:
                        if char.corporation.alliance.group:
                            chargroups.append(char.corporation.alliance.group)
                
        # Generate the list of groups to add/remove
        delgroups = set(set(self.user.groups.all()) & set(corpgroups)) - set(chargroups)
        addgroups = set(chargroups) - set(set(self.user.groups.all()) & set(corpgroups))

        print "Add: ", addgroups, "Del:", delgroups, "Current:", self.user.groups.all()
        
        for g in delgroups:
            self.user.groups.remove(g)

        for g in addgroups:
            self.user.groups.add(g)

        # For users set to not active, delete all accounts
        if not self.user.is_active:
            self._log.debug("Inactive - User %s" % (self.user))
            for servacc in ServiceAccount.objects.filter(user=self.user):
                servacc.active = 0
                servacc.save()
                pass

        # For each of the user's services, check they're in a valid group for it and enable/disable as needed.
        for servacc in ServiceAccount.objects.filter(user=self.user):
            if not (set(self.user.groups.all()) & set(servacc.service.groups.all())):
                if servacc.active:
                    servacc.active = 0
                    servacc.save()
                    self._log.debug("Disabled - User %s, Acc %s" % (self.user, servacc.service))
                    servacc.user.message_set.create(message="Your %s account has been disabled due to lack of permissions. If this is incorrect, check your API keys to see if they are valid" % (servacc.service))
                    pass
            else:
                if not servacc.active:
                    servacc.active = 1
                    servacc.save()
                    self._log.debug("Enabled - User %s, Acc %s" % (self.user, servacc.service))
                    servacc.user.message_set.create(message="Your %s account has been re-enabled, you may need to reset your password to access this service again" % (servacc.service))
                    pass

    def __str__(self):
        return self.user.__str__()

    @staticmethod
    def create_user_profile(sender, instance, created, **kwargs):   
        if created:   
            profile, created = SSOUser.objects.get_or_create(user=instance) 

    @staticmethod
    def update_service_groups(sender, instance, created, **kwargs):
        if not created:
            for acc in instance.serviceaccount_set.all():
                cls = acc.service.api_class
                cls.update_groups(acc.service_uid, instance.groups.all())

signals.post_save.connect(SSOUser.create_user_profile, sender=User)
signals.post_save.connect(SSOUser.update_service_groups, sender=User)

class Service(models.Model):
    """
    Service model represents a service available to users, either a website or
    a connection service like Jabber or IRC.
    """

    name = models.CharField("Service Name", max_length=200)
    url = models.CharField("Service URL", max_length=200, blank=True)
    active = models.BooleanField(default=True)
    api = models.CharField("API", max_length=200)
    groups = models.ManyToManyField(Group, blank=False)
    settings_json = JSONField("Service Settings", blank=True)

    @property
    def provide_login(self):
        return self.settings['provide_login']

    @property
    def api_class(self):
        api = get_api(self.api)
        api.settings = self.settings
        return api

    def __str__(self):
        return self.name

    def save(self):
        if not self.settings_json:
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

    character = None
    username = None
    password = None

    def __str__(self):
        return "%s: %s (%s)" % (self.service.name, self.user.username, self.service_uid)

    def save(self):
        """ Override default save to setup accounts as needed """

        # Grab the API class and load the settings
        api = self.service.api_class

        if not self.service_uid:
            # Create a account if we've not got a UID
            if self.active:
                # Force username to be the same as their selected character
                # Fix unicode first of all
                name = unicodedata.normalize('NFKD', self.character.name).encode('ASCII', 'ignore')

                # Remove spaces and non-acceptable characters
                self.username = re.sub('[^a-zA-Z0-9_-]+', '', name)

                if not api.check_user(self.username):
                    eveapi = None
                    for eacc in EVEAccount.objects.filter(user=self.user):
                        if self.character in eacc.characters.all():
                            eveapi = eacc
                            break

                    reddit = RedditAccount.objects.filter(user=self.user)
                    self.service_uid = api.add_user(self.username, self.password, user=self.user, character=self.character, eveapi=eveapi, reddit=reddit)
                    if not self.service_uid:
                        raise ServiceError('Error occured while trying to create the Service Account, please try again later')
                else:
                    raise ExistingUser('Username %s has already been took' % self.username)
            else:
                return

        # Disable account marked as inactive
        if self.service_uid and not self.active:
            api.disable_user(self.service_uid)

        # All went OK, save to the DB
        return models.Model.save(self)

    @staticmethod
    def pre_delete_listener( **kwargs ):
        api = kwargs['instance'].service.api_class
        if not api.delete_user(kwargs['instance'].service_uid):
            raise ServiceError('Unable to delete account on related service')

signals.pre_delete.connect(ServiceAccount.pre_delete_listener, sender=ServiceAccount)
