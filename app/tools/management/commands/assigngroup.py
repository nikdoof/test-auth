#!/usr/bin/env python

import unicodedata
import re
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from eve_api.app_defines import API_STATUS_OK
from sso.tasks import update_user_access

class Command(BaseCommand):
    help = ("Assigns a group to corporation or alliance.")

    option_list = BaseCommand.option_list + (
        make_option('-a', '--alli', action='store', dest='alliance', help='Alliance ID'),
        make_option('-c', '--corp', action='store', dest='corporation', help='Corp ID'),
        make_option('-g', '--group', action='store', dest='group', help='Group ID to assign to the corp/alliance')
    )

    requires_model_validation = False

    def handle(self, **options):

        if not options.get('alliance', None) and not options.get('corporation', None):
            raise CommandError("Please provide either a corporation or alliance")

        if options.get('alliance', None) and options.get('corporation', None):
            raise CommandError("Use either alliance or corporation, not both")

        if not options.get('group', None):
            raise CommandError("You need to specify a domain")

        alliance = options.get('alliance', None)
        corporation = options.get('corporation', None)
        group = Group.objects.get(id=options.get('group'))

        args = {'eveaccount__api_status': API_STATUS_OK}

        if alliance:
            args['eveaccount__characters__corporation__alliance__id'] = alliance
        elif corporation:
            args['eveaccount__characters__corporation__id'] = corporation

        users = User.objects.select_related('groups').filter(**args).exclude(groups__id=group.id).distinct()
        print "%s user(s) to update." % users.count()
        for user in users:
            if not group in user.groups.all():
                user.groups.add(group)
                update_user_access.delay(user.id)
        print "Done."


