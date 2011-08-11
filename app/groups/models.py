from django.db import models
from django.db.models import signals
from django.contrib.auth.models import Group, User

from groups.app_defines import *

class GroupInformation(models.Model):
    """ Extended group information """

    group = models.OneToOneField(Group)

    type = models.IntegerField("Group Type", choices=GROUP_TYPE_CHOICES, default=GROUP_TYPE_PERMISSION)
    admins = models.ManyToManyField(User, blank=True)
    public = models.BooleanField("Public", default=False, help_text="Indicates if the group is visible to all")
    requestable = models.BooleanField("Requestable", default=False, help_text="Indicates if people can request to join this group")
    moderated = models.BooleanField("Moderated", default=True, help_text="Indicates if the group requires new members to be accepted by a group admin")
    parent = models.ForeignKey(Group, related_name="children", null=True, blank=True)

    description = models.TextField(help_text="Description of the group and its permissions", blank=True)

    def save(self, *args, **kwargs):
        if self.group and (self.group.eveplayercorporation_set.count() or self.group.eveplayeralliance_set.count()):
            self.type = GROUP_TYPE_MANAGED
        models.Model.save(self, *args, **kwargs)

    @staticmethod
    def create_group(sender, instance, created, **kwargs):
        if created:
            profile, created = GroupInformation.objects.get_or_create(group=instance)

    class Meta:
        verbose_name = 'Group Information'
        verbose_name_plural = 'Group Information'
        ordering = ['group']


signals.post_save.connect(GroupInformation.create_group, sender=Group)


class GroupRequest(models.Model):
    """ Join requests for a group """

    group = models.ForeignKey(Group, null=False, related_name='requests')
    user = models.ForeignKey(User, null=False, related_name='grouprequests')
    reason = models.TextField("Reason")
    status = models.IntegerField("Request Status", choices=REQUEST_STATUS_CHOICES, null=False, default=REQUEST_PENDING)

    changed_by = models.ForeignKey(User)
    changed_date = models.DateTimeField("Changed Date/Time", auto_now=True)

    created_date = models.DateTimeField("Created Date/Time", auto_now_add=True)

    @property
    def character(self):
        char = self.user.get_profile().primary_character
        if char:
            return "[%s]%s" % (char.corporation.ticker, char.name)
        else:
            return "Unknown"

    def __unicode__(self):
        return u'%s - %s' % (self.user, self.group)

    class Meta:
        verbose_name = 'Group Access Request'
        verbose_name_plural = 'Group Access Requests'
        ordering = ['created_date']
