from django.db import models
from django.db.models import signals
from django.contrib.auth.models import Group, User

from groups.app_defines import *

class GroupInformation(models.Model):
    """ Extended group information """

    group = models.OneToOneField(Group)

    type = models.IntegerField("Group Type", choices=GROUP_TYPE_CHOICES, default=GROUP_TYPE_PERMISSION)
    admins = models.ManyToManyField(User)
    public = models.BooleanField("Public", default=False, help_text="Indicates if the group is visible to all")
    requestable = models.BooleanField("Requestable", default=False, help_text="Indicates if people can request to join this group")

    description = models.TextField(help_text="Description of the group and its permissions")

    def save(self):
        if self.group and (self.group.eveplayercorporation_set.count() or self.group.eveplayeralliance_set.count()):
            self.type = GROUP_TYPE_MANAGED
        models.Model.save(self)

    @staticmethod
    def create_group(sender, instance, created, **kwargs):
        if created:
            profile, created = GroupInformation.objects.get_or_create(group=instance)

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
