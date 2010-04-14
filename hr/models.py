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
            if choice[0] == self.status:
                return choice[1]

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
