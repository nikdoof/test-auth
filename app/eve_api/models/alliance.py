from django.db import models
from django.contrib.auth.models import Group
from eve_api.models import EVEAPIModel

class EVEPlayerAlliance(EVEAPIModel):
    """
    Represents a player-controlled alliance. Updated from the alliance
    EVE XML API puller at intervals.
    """
    name = models.CharField(max_length=255, blank=True, null=False)
    ticker = models.CharField(max_length=15, blank=True, null=False)
    executor = models.ForeignKey('eve_api.EVEPlayerCorporation', blank=True, null=True)
    member_count = models.IntegerField(blank=True, null=True)
    date_founded = models.DateField(blank=True, null=True)
    group = models.ForeignKey(Group, blank=True, null=True)

    class Meta:
        app_label = 'eve_api'
        ordering = ['date_founded']
        verbose_name = 'Alliance'
        verbose_name_plural = 'Alliances'

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return "(#%d)" % self.id
