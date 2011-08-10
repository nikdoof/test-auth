import re
from datetime import datetime
from xml.dom import minidom
from operator import itemgetter

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User

from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.conf import settings

from piston.handler import BaseHandler
from piston.utils import rc, throttle

from api.models import AuthAPIKey, AuthAPILog

from eve_proxy.models import CachedDocument
from eve_proxy.exceptions import *
from eve_api.app_defines import *
from eve_api.models import EVEAccount, EVEPlayerCharacter


class OAuthEveAPIHandler(BaseHandler):
    allowed_methods = ('GET')
    exclude = ('api_key')

    def read(self, request):
        if request.user:
            s = EVEAccount.objects.filter(user=request.user)
            return {'keys': s.values('api_user_id', 'user_id', 'api_status', 'api_last_updated')}


class OAuthOpTimerHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, id=None):

        objs = [get_object_or_404(EVEAccount, pk=settings.FULL_API_USER_ID)]

        events = []
        for obj in objs:
            params = {'userID': obj.pk, 'apiKey': obj.api_key, 'characterID': settings.FULL_API_CHARACTER_ID}
            error_doc = {'ops': [{'startsIn': -1, 'eventID': 0, 'ownerName': '', 'eventDate': '', 'eventTitle': '<div style="text-align:center">The EVE API calendar is unavailable</div>', 'duration': 0, 'isImportant': 0, 'eventText': 'Fuck CCP tbqh imho srsly', 'endsIn':-1, 'forumLink': ''}]}
            try:
                cached_doc = CachedDocument.objects.api_query('/char/UpcomingCalendarEvents.xml.aspx', params, timeout=10, service="Optimer")
            except DocumentRetrievalError:
                return error_doc
            dom = minidom.parseString(cached_doc.body.encode('utf-8'))
            if dom.getElementsByTagName('error'):
                error_doc['raw_xml'] = cached_doc.body
                return error_doc

            for node in dom.getElementsByTagName('rowset')[0].childNodes:
                if node.nodeType == 1:
                    ownerID = node.getAttribute('ownerID')                
                    if ownerID != '1':
                        date = node.getAttribute('eventDate')                
                        dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')                
                        now = datetime.utcnow()                
                        startsIn = int(dt.strftime('%s')) - int(now.strftime('%s'))
                        duration = int(node.getAttribute('duration'))

                        fid = re.search('topic=[\d]+', node.getAttribute('eventText'))
                        if fid:
                            forumlink = 'http://forum.pleaseignore.com/index.php?%s' % fid.group(0)
                        else:
                            forumlink = ''
                        #In case people forget to set a duration, we'll give a default of 1 hour
                        if duration == 0:
                            duration = 60
                        endsIn = startsIn + (duration * 60)
                        if startsIn < 0:
                            startsIn = 0
                        if endsIn > 0:
                            event = {
                                'startsIn': startsIn,
                                'eventID': int(node.getAttribute('eventID')),
                                'ownerName': node.getAttribute('ownerName'),
                                'eventDate': date,
                                'eventTitle': node.getAttribute('eventTitle'),
                                'duration': duration,
                                'isImportant': int(node.getAttribute('importance')),
                                'eventText': node.getAttribute('eventText'),
                                'endsIn':endsIn,
                                'forumLink': forumlink}                
                            events.append(event)

        if len(events) == 0:
            return {'ops':[{
                'startsIn': -1,
                'eventID': 0,
                'ownerName': '',
                'eventDate': '',
                'eventTitle': '<div style="text-align:center">No ops are currently scheduled</div>',
                'duration': 0,
                'isImportant': 0,
                'eventText': 'Add ops using EVE-Gate or the in-game calendar',
                'endsIn':-1,
                'forumLink': ''}]}
        else:
            events.sort(key=itemgetter('startsIn'))
            return {'ops': events, 'doc_time': cached_doc.time_retrieved, 'cache_until': cached_doc.cached_until, 'current_time': datetime.utcnow() }


class OAuthCharacterHandler(BaseHandler):
    allowed_methods = ('GET')

    fields = ('id', 'name', ('corporation', ('id', 'name', ('alliance', ('id', 'name')))), 'corporation_date', 'balance', 'total_sp', 'security_status', 'director', 'skillset')

    @classmethod
    def skillset(cls, instance):
        return instance.eveplayercharacterskill_set.all().values('skill__id', 'skill__name', 'level', 'skillpoints')

    def read(self, request):
        return EVEPlayerCharacter.objects.filter(eveaccount__user=request.user)
