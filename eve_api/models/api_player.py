"""
This module holds data from the EVE XML API.
"""
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User, Group
from eve_proxy.models import CachedDocument
from eve_api.managers import EVEPlayerCorporationManager, EVEPlayerAllianceManager, EVEPlayerCharacterManager
from eve_api.app_defines import API_STATUS_CHOICES, API_STATUS_PENDING, API_RACES_CHOICES, API_GENDER_CHOICES

class EVEAPIModel(models.Model):
    """
    A simple abstract base class to set some consistent fields on the models
    that are updated from the EVE API.
    """
    api_last_updated = models.DateTimeField(blank=True, null=True,
                                            verbose_name="Time last updated from API",
                                            help_text="When this object was last updated from the EVE API.")
    
    class Meta:
        abstract = True

class EVEAccount(EVEAPIModel):
    """
    Use this class to store EVE user account information. Note that its use is
    entirely optional and up to the developer's discretion.
    """
    user = models.ForeignKey(User, blank=True, null=True,
                             help_text="User that owns this account")
    description = models.CharField(max_length=50, blank=True,
                                   help_text="User-provided description.")
    api_key = models.CharField(max_length=64, verbose_name="API Key")
    api_user_id = models.IntegerField(verbose_name="API User ID")
    characters = models.ManyToManyField("EVEPlayerCharacter", blank=True,
                                        null=True)
    api_status = models.IntegerField(choices=API_STATUS_CHOICES,
                                     default=API_STATUS_PENDING,
                                     verbose_name="API Status",
                                     help_text="End result of the last attempt at updating this object from the API.")

    @property
    def api_status_description(self):
        for choice in API_STATUS_CHOICES:
            if choice[0] == self.api_status:
                return choice[1]

    def in_corp(self, corpid):
        for char in self.characters.all():
            if char.corporation_id == corpid:
                return True
        return False

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'EVE Account'
        verbose_name_plural = 'EVE Accounts'
        ordering = ['api_user_id']
        
class EVEPlayerCharacter(EVEAPIModel):
    """
    Represents an individual player character within the game. Not to be
    confused with an account.
    """
    name = models.CharField(max_length=255, blank=True, null=False)
    corporation = models.ForeignKey('EVEPlayerCorporation', blank=True, null=True)
    race = models.IntegerField(blank=True, null=True, choices=API_RACES_CHOICES)
    gender = models.IntegerField(blank=True, null=True, choices=API_GENDER_CHOICES)
    balance = models.FloatField("Account Balance", blank=True, null=True)
    attrib_intelligence = models.IntegerField("Intelligence", blank=True, 
                                              null=True)
    attrib_memory = models.IntegerField("Memory", blank=True, null=True)
    attrib_charisma = models.IntegerField("Charisma", blank=True, null=True)
    attrib_perception = models.IntegerField("Perception", blank=True, null=True)
    attrib_willpower = models.IntegerField("Willpower", blank=True, null=True)

    total_sp = models.IntegerField("Total SP", blank=True, null=True)
    
    objects = EVEPlayerCharacterManager()
    
    @property
    def gender_description(self):
        for choice in API_GENDER_CHOICES:
            if choice[0] == self.gender:
                return choice[1]

    @property
    def race_description(self):
        for choice in API_RACES_CHOICES:
            if choice[0] == self.race:
                return choice[1]

    def __unicode__(self):
        if self.name:
            return "%s (%d)" % (self.name, self.id)
        else:
            return "(%d)" % self.id

    def __str__(self):
        return self.__unicode__()
    
    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Player Character'
        verbose_name_plural = 'Player Characters'

class EVEPlayerAlliance(EVEAPIModel):
    """
    Represents a player-controlled alliance. Updated from the alliance
    EVE XML API puller at intervals.
    """
    name = models.CharField(max_length=255, blank=True, null=False)
    ticker = models.CharField(max_length=15, blank=True, null=False)
    #executor_character = models.ForeignKey(EVECharacter, blank=True, null=False)
    member_count = models.IntegerField(blank=True, null=True)
    date_founded = models.DateField(blank=True, null=True)
    
    objects = EVEPlayerAllianceManager()
    
    class Meta:
        app_label = 'eve_api'
        ordering = ['date_founded']
        verbose_name = 'Player Alliance'
        verbose_name_plural = 'Player Alliances'
    
    def __unicode__(self):
        if self.name:
            return "%s (%d)" % (self.name, self.id)
        else:
            return "(#%d)" % self.id
        
    def __str__(self):
        return self.__unicode__()

class EVEPlayerCorporation(EVEAPIModel):
    """
    Represents a player-controlled corporation. Updated from a mixture of
    the alliance and corporation API pullers.
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    ticker = models.CharField(max_length=15, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(verify_exists=False, blank=True, null=True)
    ceo_character = models.ForeignKey(EVEPlayerCharacter, blank=True, null=True)
    #home_station = models.ForeignKey(EVEStation, blank=True, null=False)
    alliance = models.ForeignKey(EVEPlayerAlliance, blank=True, null=True)
    alliance_join_date = models.DateField(blank=True, null=True)
    tax_rate = models.FloatField(blank=True, null=True)
    member_count = models.IntegerField(blank=True, null=True)
    shares = models.IntegerField(blank=True, null=True)
    
    # Logo generation stuff
    logo_graphic_id = models.IntegerField(blank=True, null=True)
    logo_shape1 = models.IntegerField(blank=True, null=True)
    logo_shape2 = models.IntegerField(blank=True, null=True)
    logo_shape3 = models.IntegerField(blank=True, null=True)
    logo_color1 = models.IntegerField(blank=True, null=True)
    logo_color2 = models.IntegerField(blank=True, null=True)
    logo_color3 = models.IntegerField(blank=True, null=True)

    group = models.ForeignKey(Group, blank=True, null=True)
    applications = models.BooleanField(blank=False, default=False)

    objects = EVEPlayerCorporationManager()
    
    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Player Corporation'
        verbose_name_plural = 'Player Corporations'

    def __str__(self):
        if self.name:
            return self.name
        else:
            return "Corp #%d" % self.id
        
    def query_and_update_corp(self):
        """
        Takes an EVEPlayerCorporation object and updates it from the 
        EVE API service.
        """
        # Pull XML from the EVE API via eve_proxy.
        dom = EVEPlayerCorporation.objects.api_corp_sheet_xml(self.id)
        
        # Tuples of pairings of tag names and the attribute on the Corporation
        # object to set the data to.
        tag_mappings = (
            ('corporationName', 'name'),
            ('ticker', 'ticker'),
            ('url', 'url'),
            ('description', 'description'),
            ('memberCount', 'member_count'),
            ('graphicID', 'logo_graphic_id'),
            ('shape1', 'logo_shape1'),
            ('shape2', 'logo_shape2'),
            ('shape3', 'logo_shape3'),
            ('color1', 'logo_color1'),
            ('color2', 'logo_color2'),
            ('color3', 'logo_color3'),
        )
        
        # Iterate through the tag mappings, setting the values of the tag names
        # (first member of the tuple) to the attribute named in the second member
        # of the tuple on the EVEPlayerCorporation object.
        for tag_map in tag_mappings:
            try:
                setattr(self, tag_map[1], 
                        dom.getElementsByTagName(tag_map[0])[0].firstChild.nodeValue)
            except AttributeError:
                # This tag has no value, skip it.
                continue
            except IndexError:
                # Something weird has happened
                continue

        self.api_last_updated = datetime.utcnow()
        self.save()
