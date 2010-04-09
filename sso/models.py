import re
import unicodedata
import logging

from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User, UserManager, Group
from eve_api.models import EVEAccount, EVEPlayerCorporation
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
        # Create a list of all Corp groups
        corpgroups = []
        for corp in EVEPlayerCorporation.objects.filter(group__isnull=False):
            if corp.group:
                corpgroups.append(corp.group)  
        
        # Create a list of Char groups
        chargroups = []
        for eacc in EVEAccount.objects.filter(user=self.user):
            if eacc.api_status == 1:
                for char in eacc.characters.all():
                    if char.corporation.group:
                        chargroups.append(char.corporation.group)
                
        # Generate the list of groups to add/remove
        delgroups = set(set(self.user.groups.all()) & set(corpgroups)) - set(chargroups)
        addgroups = set(chargroups) - set(set(self.user.groups.all()) & set(corpgroups))
        
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

signals.post_save.connect(SSOUser.create_user_profile, sender=User)

class Service(models.Model):
    name = models.CharField("Service Name", max_length=200)
    url = models.CharField("Service URL", max_length=200, blank=True)
    active = models.BooleanField(default=True)
    api = models.CharField("API", max_length=200)
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
    service_uid = models.CharField("Service UID", max_length=200, blank=False)
    active = models.BooleanField(default=True)

    character = None
    username = None
    password = None

    def __str__(self):
        return "%s: %s (%s)" % (self.service.name, self.user.username, self.service_uid)

    def save(self):
        """ Override default save to setup accounts as needed """

        # Grab the API class
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
