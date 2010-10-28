from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

from eve_api.models import EVEPlayerCharacter, EVEPlayerCorporation

from hr.app_defines import *

class Application(models.Model):
    user = models.ForeignKey(User, blank=False, verbose_name="User")
    character = models.ForeignKey(EVEPlayerCharacter, blank=False, verbose_name="Character")
    corporation = models.ForeignKey(EVEPlayerCorporation, blank=False, verbose_name="Applying to Corporation")
    status = models.IntegerField(choices=APPLICATION_STATUS_CHOICES,
                                     default=APPLICATION_STATUS_NOTSUBMITTED,
                                     verbose_name="Status",
                                     help_text="Current status of this application request.")

    @property
    def blacklisted(self):
        if len(self.blacklist_values) > 0:
            return True
        return False

    @property
    def blacklist_values(self):
        """
        Returns a list of blacklist values that apply to the application
        """

        blacklist = []

        bl_items = Blacklist.objects.filter( models.Q(expiry_date__gt=datetime.now()) | models.Q(expiry_date=None) )

        # Check Reddit blacklists
        reddit_uids = self.user.redditaccount_set.all().values_list('username')
        reddit = [a[0].lower() for a in reddit_uids if a and a[0]]
        objs = bl_items.filter(type=BLACKLIST_TYPE_REDDIT, value__in=reddit)
        blacklist.extend(objs)

        # Check email blacklists
        blacklist.extend(bl_items.filter(type=BLACKLIST_TYPE_EMAIL, value=self.user.email.lower()))

        # Check Auth blacklists
        blacklist.extend(bl_items.filter(type=BLACKLIST_TYPE_AUTH, value=self.user.username.lower()))

        # Check EVE Related blacklists
        evechars = EVEPlayerCharacter.objects.filter(eveaccount__user=self.user).select_related('corporation__alliance')

        # Check Character blacklists
        chars = [a[0].lower() for a in evechars.values_list('name') if a and a[0]]
        objs = bl_items.filter(type=BLACKLIST_TYPE_CHARACTER, value__in=chars)
        blacklist.extend(objs)

        # Check Corporation blacklists
        corps = [a[0].lower() for a in evechars.values_list('corporation__name') if a and a[0]]
        objs = bl_items.filter(type=BLACKLIST_TYPE_CORPORATION, value__in=corps)
        blacklist.extend(objs)

        # Check Alliance blacklists
        alliances = [a[0].lower() for a in evechars.values_list('corporation__alliance__name') if a and a[0]]

        objs = bl_items.filter(type=BLACKLIST_TYPE_ALLIANCE, value__in=alliances)
        blacklist.extend(objs)

        return blacklist

    def save(self, *args, **kwargs):

        user = None
        if 'user' in kwargs:
            user = kwargs['user']
            del kwargs['user']

        try:
            old_instance = Application.objects.get(id=self.id)
            if not (old_instance.status == int(self.status)):
                event = Audit(application=self)
                event.user = user
                event.event = AUDIT_EVENT_STATUSCHANGE

                # Save the application so we can get a up to date status
                super(Application, self).save(*args, **kwargs)
                new_instance = Application.objects.get(id=self.id)

                event.text = "Status changed from %s to %s" % (old_instance.get_status_display(), new_instance.get_status_display())
                event.save()
        except:
            pass

        super(Application, self).save(*args, **kwargs)


    def __unicode__(self):
        return self.character.name

    def __str__(self):
        return self.__unicode__()

class Recommendation(models.Model):
    user = models.ForeignKey(User, blank=False, verbose_name="User")
    user_character = models.ForeignKey(EVEPlayerCharacter, blank=False, verbose_name="Recommender")
    application = models.ForeignKey(Application, blank=False, verbose_name="Recommended Application")

    def __unicode__(self):
        return self.user_character.name

    def __str__(self):
        return self.__unicode__()

class Audit(models.Model):
    application = models.ForeignKey(Application, blank=False, verbose_name="Application")
    user = models.ForeignKey(User, blank=True, verbose_name="User")
    event = models.IntegerField(choices=AUDIT_EVENT_CHOICES,
                                     verbose_name="Event Type",
                                     help_text="Type of audit event")
    text = models.TextField(blank=False, verbose_name="Event Text",
                                     help_text="Detailed event text")

    date = models.DateTimeField(auto_now_add=True, verbose_name="Event Date")


class Blacklist(models.Model):
    type = models.IntegerField(choices=BLACKLIST_TYPE_CHOICES,
                                     verbose_name="Blacklisted Type",
                                     help_text="Type of entity to be blacklisted")
    value = models.CharField("Blacklisted Value", max_length=255, blank=False)
    reason = models.TextField(blank=False, verbose_name="Reason",
                                     help_text="Reason that the entity was blacklisted")

    expiry_date = models.DateTimeField(verbose_name="Expiry Date", blank=False, null=True,
                                     help_text="Date to expire this entry")

    source = models.IntegerField(choices=BLACKLIST_SOURCE_CHOICES,
                                     verbose_name="Blacklist Source",
                                     help_text="Source of the blacklisted item",
                                     default=BLACKLIST_SOURCE_INTERNAL)

    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Created Date")
    created_by = models.ForeignKey(User, blank=False, verbose_name="Created By")

    def __unicode__(self):
        return u'%s: %s' % (self.get_type_display(), self.value)

    def __str__(self):
        return self.__unicode__()
