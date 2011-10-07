#!/usr/bin/env python
import os

# Set niceness
os.nice(20)

# Activate the virtualenv
path = os.path.dirname(os.path.realpath(__file__))
activate_this = os.path.join(path, 'env/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

import sys
import logging
from django.core.management import setup_environ
from django.conf import settings

setup_environ(settings)

import getopt

from django.db.models import Count
from django.core.cache import cache
from eve_api.app_defines import *
from eve_api.models import EVEAccount, EVEPlayerCorporation

from hr.app_defines import *
from hr.models import Application

from eve_proxy.models import CachedDocument

accepted_names = ['munin.py', 'auth_apikeys', 'auth_hrapplications',
                  'auth_eveapicache']


class Usage(Exception):
    pass


def main(argv=None):
    if argv is None:
        argv = sys.argv

    if os.path.basename(argv[0]) in accepted_names:
        execname = os.path.basename(argv[0])
    else:
        print argv[0]
        print >> sys.stderr, "Invalid symlink name, check the source"
        return 2
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "", ["config"])
        except getopt.error, msg:
            raise Usage(msg)
        # more code, unchanged
    except Usage, err:
        print >> sys.stderr, "Invalid usage"
        return 2

    for arg in args:
        if arg == 'config':
            if execname == 'auth_apikeys':
                print "graph_title Auth Active EVE API Keys"
                print "graph_vlabel Keys"
                print "graph_category auth"
                print "keys.label Keys"
                print "graph_args --base 1000"
                return 0
            if execname == 'auth_hrapplications':
                print "graph_title Auth - Open Applications"
                print "graph_vlabel Applications"
                print "graph_category auth"

                for i, n in EVEPlayerCorporation.objects.filter(application_config__is_accepting=True).values_list('id', 'name'):
                    print "%s.label %s" % (i, n)
                    print "%s.warning 10" % i
                    print "%s.critical 20" % i
                print "graph_args --base 1000"
                return 0
            if execname == 'auth_eveapicache':
                print "graph_title Auth - Cached EVE API Requests"
                print "graph_vlabel Cached Requests"
                print "graph_category auth"
                print "requests.label Cached Requests"
                print "graph_args --base 1000"
                return 0
            if execname == 'auth_api_proxy_requests':
                print "graph_title Auth - EVE API Requests"
                print "graph vlabel Requests"
                print "graph_category auth"
                print "eve_proxy_api_requests.label API Requests"
                print "eve_proxy_api_requests.type COUNTER"

    if execname == 'auth_apikeys':
        key_count = EVEAccount.objects.filter(api_status=API_STATUS_OK).count()
        print "keys.value %s" % key_count
    elif execname == 'auth_hrapplications':
        view_status = [APPLICATION_STATUS_AWAITINGREVIEW,
                       APPLICATION_STATUS_ACCEPTED, APPLICATION_STATUS_QUERY, APPLICATION_STATUS_FLAGGED]

        corps = EVEPlayerCorporation.objects.filter(application_config__is_accepting=True, application__status__in=view_status).annotate(num_apps=Count('application')).values_list('id', 'num_apps')
        for c,n in corps:
            print "%s.value %s" % (c, n)
    elif execname == 'auth_eveapicache':
        print "requests.value %s" % CachedDocument.objects.count()

    elif execname == 'auth_api_proxy_requests':
        print "eve_proxy_api_requests.value %s" % cache.get('eve_proxy_api_requests', 0)


if __name__ == "__main__":
    sys.exit(main())
