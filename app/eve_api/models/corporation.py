from django.db import models
from django.contrib.auth.models import Group
from eve_api.models import EVEAPIModel

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
    applications = models.BooleanField(blank=False, default=False)

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Player Corporation'
        verbose_name_plural = 'Player Corporations'

    def __str__(self):
        if self.name:
            return self.name
        else:
            return "Corp #%d" % self.id

