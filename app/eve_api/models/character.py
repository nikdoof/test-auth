from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from eve_api.app_defines import *
from eve_api.models import EVEAPIModel


class EVEPlayerCharacterSkill(models.Model):
    """
    For our m2m join to EVESkills
    """
    character = models.ForeignKey('eve_api.EVEPlayerCharacter')
    skill = models.ForeignKey('eve_api.EVESkill')
    level = models.IntegerField(default=0)
    skillpoints = models.IntegerField(default=0)
    in_training = models.IntegerField(default=0)

    def __unicode__(self):
        return u"%s - Level %s" % (self.skill, self.level)

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Player Character Skill'
        verbose_name_plural = 'Player Character Skills'


class EVEPlayerCharacterEmploymentHistory(models.Model):
    """
    Player's corporation history
    """
    record_id = models.IntegerField(primary_key=True, verbose_name="Record ID")
    character = models.ForeignKey('eve_api.EVEPlayerCharacter', related_name='employmenthistory')
    corporation = models.ForeignKey('eve_api.EVEPlayerCorporation', related_name='+')
    start_date = models.DateTimeField(blank=False, null=False, verbose_name="Corporation Join Date")

    @property
    def end_date(self):
        if self.character.employmenthistory.filter(record_id__gt=self.record_id).count():
            return self.character.employmenthistory.filter(record_id__gt=self.record_id)[0].start_date
        return None

    def __unicode__(self):
        return u'%s - %s - %s' % (self.record_id, self.character, self.corporation)

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Player Character Employment History'
        verbose_name_plural = 'Player Character Employment Histories'


class EVEPlayerCharacter(EVEAPIModel):
    """
    Represents an individual player character within the game. Not to be
    confused with an account.
    """
    name = models.CharField(max_length=255, blank=True, null=False)
    corporation = models.ForeignKey('eve_api.EVEPlayerCorporation', blank=True, null=True)
    corporation_date = models.DateTimeField(blank=True, null=True, verbose_name="Corporation Join Date")
    race = models.IntegerField(blank=True, null=True, choices=API_RACES_CHOICES)
    gender = models.IntegerField(blank=True, null=True, choices=API_GENDER_CHOICES)
    balance = models.FloatField("Account Balance", blank=True, null=True)
    attrib_intelligence = models.IntegerField("Intelligence", blank=True, null=True)
    attrib_memory = models.IntegerField("Memory", blank=True, null=True)
    attrib_charisma = models.IntegerField("Charisma", blank=True, null=True)
    attrib_perception = models.IntegerField("Perception", blank=True, null=True)
    attrib_willpower = models.IntegerField("Willpower", blank=True, null=True)
    total_sp = models.IntegerField("Total SP", blank=True, null=True)
    security_status = models.FloatField("Security Status", blank=True, null=True)
    current_location_id = models.IntegerField("Current Location ID", blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True,
                                            verbose_name="Last Login Date/Time",
                                            help_text="The last time this character logged into EVE")
    last_logoff = models.DateTimeField(blank=True, null=True, verbose_name="Last Logoff Date/Time",
                                            help_text="The last time this character logged off EVE")
    roles = models.ManyToManyField('eve_api.EVEPlayerCharacterRole', blank=True, null=True,
                                            help_text="Roles associated with this character")
    skills = models.ManyToManyField('eve_api.EVESkill', through='eve_api.EVEPlayerCharacterSkill')

    @property
    def director(self):
        """ Returns a bool to indicate if the character is a director """
        try:
            self.roles.get(name="roleDirector")
            return True
        except ObjectDoesNotExist:
            return False

    @property
    def current_training(self):
        """ Returns the current skill in training """
        try:
            return self.eveplayercharacterskill_set.get(in_training__gt=0)
        except EVEPlayerCharacterSkill.DoesNotExist:
            return None

    @property
    def account(self):
        if self.eveaccount_set.filter(api_status=API_STATUS_OK).count():
            return self.eveaccount_set.filter(api_status=API_STATUS_OK)[0]
        return None

    @property
    def active_key(self):
        if self.eveaccount_set.count():
            return self.eveaccount_set.filter(api_status=API_STATUS_OK).count() > 0
        return False

    @models.permalink
    def get_absolute_url(self):
        return ('eveapi-character', [self.pk])

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return u"(%d)" % self.id

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Character'
        verbose_name_plural = 'Characters'

        permissions = (
            ("can_view_all_characters", "Can view any character profile"),
        )
