from django.db import IntegrityError
from django.contrib.auth import logout
from django.utils.timezone import utc, now

class InactiveLogoutMiddleware(object):
    """
    Detect inactive and logged in users and log them out
    """

    def process_request(self, request):
        if request.user.is_authenticated() and not request.user.is_active:
            logout(request)


class IGBMiddleware(object):
    """
    Middleware to detect the EVE IGB
    """

    def process_request(self, request):

        request.is_igb = False
        request.is_igb_trusted = False

        header_map = [
            ('HTTP_EVE_SERVERIP', 'eve_server_ip'),
            ('HTTP_EVE_CHARNAME', 'eve_charname'),
            ('HTTP_EVE_CHARID', 'eve_charid'),
            ('HTTP_EVE_CORPNAME', 'eve_corpname'),
            ('HTTP_EVE_CORPID', 'eve_corpid'),
            ('HTTP_EVE_ALLIANCENAME', 'eve_alliancename'),
            ('HTTP_EVE_ALLIANCEID', 'eve_allianceid'),
            ('HTTP_EVE_REGIONNAME', 'eve_regionid'),
            ('HTTP_EVE_CONSTELLATIONNAME', 'eve_constellationname'),
            ('HTTP_EVE_SOLARSYSTEMNAME', 'eve_systemname'),
            ('HTTP_EVE_STATIONNAME,', 'eve_stationname'),
            ('HTTP_EVE_STATIONID,', 'eve_stationid'),
            ('HTTP_EVE_CORPROLE,', 'eve_corprole'),
        ]

        if request.META.has_key('HTTP_EVE_TRUSTED'):
            request.is_igb = True
            if request.META.get('HTTP_EVE_TRUSTED') == 'Yes':
                request.is_igb_trusted = True
    
                for header, map in header_map:
                    if request.META.get(header, None):
                        setattr(request, map, request.META.get(header, None))
                            

from datetime import datetime

class IPTrackingMiddleware(object):
    """
    Middleware to track user's IPs and insert them into the database
    """

    def process_request(self, request):
        from sso.models import SSOUserIPAddress

        if request.user and not request.user.is_anonymous():
            ip, created = SSOUserIPAddress.objects.get_or_create(user=request.user, ip_address=request.META['REMOTE_ADDR'])
            ip.last_seen = now()
            ip.save()
