from django.db import models
from django.contrib.auth.models import Group
from eve_api.models import EVEAPIModel
from eve_api.app_defines import *

class EVEPlayerCorporation(EVEAPIModel):
    """
    Represents a player-controlled corporation. Updated from a mixture of
    the alliance and corporation API pullers.
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    ticker = models.CharField(max_length=15, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(verify_exists=False, blank=True, null=True)
    ceo_character = models.ForeignKey('eve_api.EVEPlayerCharacter', blank=True, null=True)
    alliance = models.ForeignKey('eve_api.EVEPlayerAlliance', blank=True, null=True)
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

    @property
    def directors(self):
        """ Return a queryset of corporate Directors """
        return self.eveplayercharacter_set.filter(roles__name="roleDirector")

    @property
    def api_keys(self):
        """ Returns the number of characters with stored API keys """
        return self.eveplayercharacter_set.filter(eveaccount__isnull=False).count()

    @property
    def director_api_keys(self):
        return self.directors.filter(eveaccount__isnull=False, eveaccount__api_keytype=API_KEYTYPE_FULL, eveaccount__api_status=API_STATUS_OK)

    @property
    def api_key_coverage(self):
        """ Returns the percentage coverage of API keys for the corporation's members """

        # Check if we have a full director key, see if we can base our assumptions off what is in auth already
        if self.director_api_keys.count():
            membercount = self.eveplayercharacter_set.count()
        else:
            membercount = self.member_count
        return (float(self.api_keys) / membercount) * 100

    @models.permalink
    def get_absolute_url(self):
        return ('eveapi-corporation', [self.pk])

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Player Corporation'
        verbose_name_plural = 'Player Corporations'

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return u"Corp #%d" % self.id

