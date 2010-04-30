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
    def status_description(self):
        for choice in APPLICATION_STATUS_CHOICES:
            if choice[0] == int(self.status):
                return choice[1]

    def save(self, *args, **kwargs):
        try:
            old_instance = Application.objects.get(id=self.id)
            if not (old_instance.status == int(self.status)):
                event = Audit(application=self)
                if 'user' in kwargs:
                    event.user = kwargs['user']
                event.event = AUDIT_EVENT_STATUSCHANGE

                event.text = "Status changed from %s to %s" % (old_instance.status_description, self.status_description)
                event.save()
        except:
            pass

        if 'user' in kwargs:
            del kwargs['user']
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

    def event_description(self):
        return AUDIT_EVENT_LOOKUP[self.event]
