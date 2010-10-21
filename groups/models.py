from django.db import models
from django.db.models import signals
from django.contrib.auth.models import Group, User

from groups.app_defines import *

class GroupInformation(models.Model):
    """ Extended group information """

    group = models.OneToOneField(Group)

    type = models.IntegerField("Group Type", choices=GROUP_TYPE_CHOICES, default=GROUP_TYPE_BUILTIN)
    admins = models.ManyToManyField(User)
    public = models.BooleanField("Public", default=False)
    requestable = models.BooleanField("Requestable", default=False)

    description = models.TextField()

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
