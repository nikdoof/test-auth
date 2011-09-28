#!/usr/bin/env python

import unicodedata
import re
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from eve_api.models import EVEPlayerCharacter
from eve_api.app_defines import API_STATUS_OK

class Command(BaseCommand):
    help = ("Extracts a list of emails for a corp domain")

    option_list = BaseCommand.option_list + (
        make_option('-a', '--alli', action='store', dest='alliance', help='Alliance ID of the extract'),
        make_option('-c', '--corp', action='store', dest='corporation', help='Corp ID of the extract'),
        make_option('-d', '--domain', action='store', dest='domain', help='Domain of the extract')
    )

    requires_model_validation = False

    def handle(self, **options):

        if not options.get('alliance', None) and not options.get('corporation', None):
            raise CommandError("Please provide either a corporation or alliance")

        if options.get('alliance', None) and options.get('corporation', None):
            raise CommandError("Use either alliance or corporation, not both")

        if not options.get('domain', None):
            raise CommandError("You need to specify a domain")

        alliance = options.get('alliance', None)
        corporation = options.get('corporation', None)
        domain = options.get('domain', None)

        chars = EVEPlayerCharacter.objects.select_related('eveaccount__user').filter(eveaccount__api_status=API_STATUS_OK, eveaccount__isnull=False).distinct()
        if alliance:
             chars = chars.filter(corporation__alliance__id=alliance)
        elif corporation:
             chars = chars.filter(corporation__id=corporation)

        for char in chars:
             charname = re.sub('[^a-zA-Z0-9_-]+', '', unicodedata.normalize('NFKD', char.name).encode('ASCII', 'ignore'))
             if charname and char.eveaccount_set.all()[0].user.email:
                 print "%s@%s\t%s" % (charname.lower(), domain, char.eveaccount_set.all()[0].user.email)
