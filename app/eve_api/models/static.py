"""
This file covers any static information from the EVE data dumps. While
using django-evedb would be a smarter choice, for the limited subset of
data we're using it isn't worth the overhead
"""

from django.db import models


class EVESkill(models.Model):
    """ Represents a skill in EVE Online """

    name = models.CharField(blank=True, max_length=255)
    group = models.ForeignKey('eve_api.EVESkillGroup', null=True)
    description = models.TextField(blank=True)    

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return u"Skill %d" % self.id

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Character Skill'
        verbose_name_plural = 'Character Skills'


class EVESkillGroup(models.Model):
    """ Represents a skill group in EVE Online """

    name = models.CharField(blank=True, max_length=255)

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return u"Skill Group %d" % self.id

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Character Skill Group'
        verbose_name_plural = 'Character Skill Groups'


class EVEPlayerCharacterRole(models.Model):
    """
    Represents a role which can be applied to a character
    """

    roleid = models.CharField(max_length=64, blank=False, null=False)
    name = models.CharField(max_length=255, blank=False, null=False)

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return u"Role %d" % self.id

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'Character Role'
        verbose_name_plural = 'Character Roles'

