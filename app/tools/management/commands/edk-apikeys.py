#!/usr/bin/env python2.5

from django.core.management.base import NoArgsCommand
from eve_api.models import EVEPlayerCharacter
from eve_api.app_defines import *

class Command(NoArgsCommand):
    help = "Extracts a list of director's full API keys in CSV format for uploading to EDK"

    def handle_noargs(self, **options):
        chars = EVEPlayerCharacter.objects.filter(director=True, eveaccount__api_keytype=API_KEYTYPE_FULL, eveaccount__api_status=API_STATUS_OK)
        donekeys = []

        i = 0
        for c in chars:
            i = i + 1
            print "\"TEST\",\"API_CharID_%s\",\"%s\"" % (i, c.id)
            print "\"TEST\",\"API_UserID_%s\",\"%s\"" % (i, c.eveaccount_set.all()[0].id)
            print "\"TEST\",\"API_Key_%s\",\"%s\"" % (i, c.eveaccount_set.all()[0].api_key)
            print "\"TEST\",\"API_Name_%s\",\"%s - %s\"" % (i, c.corporation.name, c.name)
            print "\"TEST\",\"API_Type_%s\",\"corp\"" % (i)
            print "\"TEST\",\"API_Key_count\",\"%s\"" % i
