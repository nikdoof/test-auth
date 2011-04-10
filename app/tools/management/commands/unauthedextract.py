#!/usr/bin/env python

import unicodedata
import re
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from eve_api.models import EVEPlayerCharacter

class Command(BaseCommand):
    help = ("Provides a list of characters with no API key for a corp")

    option_list = BaseCommand.option_list + (
        make_option('-c', '--corp', action='store', dest='corporation', help='Corp ID of the extract'),
    )

    requires_model_validation = False

    def handle(self, **options):

        if not options.get('corporation', None):
            raise CommandError("Please provide a corporation")

        corporation = options.get('corporation', None)

        chars = EVEPlayerCharacter.objects.filter(corporation__id=corporation, eveaccount__isnull=True)

        print "Character,Last Login,Total SP,Location ID"
        for char in chars:
            print "%s,%s,%s,%s" % (char.name, char.last_login, char.total_sp, char.current_location_id)
