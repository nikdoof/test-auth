import re
from datetime import datetime

from piston.handler import BaseHandler
from piston.utils import rc, throttle

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User

from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from api.models import AuthAPIKey, AuthAPILog
from eve_proxy.models import CachedDocument
from eve_api.models import EVEAccount
from sso.models import ServiceAccount, Service

from settings import FULL_API_USER_ID
from settings import FULL_API_CHARACTER_ID

from xml.dom import minidom


class UserHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, id=None):
        if id:
            try:
                u = User.objects.get(id=id)
            except (User.DoesNotExist, ValueError):
                return { 'auth': 'missing', 'missing': 'userid'}
        elif 'user' in request.GET:
            try:
                u = User.objects.get(username=request.GET['user'])
            except User.DoesNotExist:
                return { 'auth': 'missing', 'missing': 'username'}
        elif 'serviceuid' in request.GET:
            try:
                u = ServiceAccount.objects.get(service_uid=request.GET['serviceuid']).user
            except ServiceAccount.DoesNotExist:
                return { 'auth': 'missing', 'missing': 'ServiceAccount'}

        chars = []
        for a in u.eveaccount_set.all():
            chars.extend(a.characters.all())

        d = { 'id': u.id, 'username': u.username, 'email': u.email,
              'serviceaccounts': u.serviceaccount_set.all(), 'characters': chars,
              'groups': u.groups.all(), 'staff': u.is_staff, 'superuser': u.is_superuser }

        return d


class LoginHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, id=None):

        u = None
        if id:
            try:
                u = User.objects.get(id=id)
            except (User.DoesNotExist, ValueError):
                return { 'auth': 'missing', 'missing': 'UserID' }

        if request.GET.get('user', None):
            try:
                u = User.objects.get(username=request.GET['user'])
            except User.DoesNotExist:
                return { 'auth': 'missing', 'missing': 'Username' }

        if u:
            if request.GET.get('pass', None) and request.GET['pass'] == u.get_profile().api_service_password:
                return { 'auth': 'ok', 'id': u.id, 'username': u.username,
                         'email': u.email, 'groups': u.groups.all(),
                         'staff': u.is_staff, 'superuser': u.is_superuser }
            else:
                return { 'auth': 'failed' }

        return { 'auth': 'missing', 'missing': 'all' }


class EveAPIHandler(BaseHandler):
    allowed_methods = ('GET')
    exclude = ('api_key')

    def read(self, request):
       if request.GET.get('id', None):
           s = get_object_or_404(EVEAccount, pk=id)
       elif request.GET.get('userid', None):
           s = EVEAccount.objects.filter(user=request.GET['userid'])
       elif request.GET.get('corpid', None):
           s = EVEAccount.objects.filter(characters__corporation__id=request.GET['corpid'])
       elif request.GET.get('allianceid', None):
           s = EVEAccount.objects.filter(characters__corporation__alliance__id=request.GET['allianceid'])

       return { 'keys': s.values('id', 'user_id', 'api_status', 'api_last_updated') }

class EveAPIProxyHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):
        url_path = request.META['PATH_INFO'].replace(reverse('api-eveapiproxy'),"/")

        params = {}
        for key,value in request.GET.items():
            params[key.lower()] = value

        if 'userid' in params:
            obj = get_object_or_404(EVEAccount, pk=params['userid'])
            params['apikey'] = obj.api_key

        cached_doc = CachedDocument.objects.api_query(url_path, params, exceptions=False)

        return HttpResponse(cached_doc.body)
    
class OpTimerHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, id=None):
        obj = get_object_or_404(EVEAccount, id=FULL_API_USER_ID)
            
        params = {'userID':obj.id,'apiKey':obj.api_key,'characterID':FULL_API_CHARACTER_ID}
        
        cached_doc = CachedDocument.objects.api_query('/char/UpcomingCalendarEvents.xml.aspx', params, exceptions=False)
        
        dom = minidom.parseString(cached_doc.body.encode('utf-8'))
        enode = dom.getElementsByTagName('error')
        if enode:
            return {'ops':[{
                'startsIn': -1,
                'eventID': 0,
                'ownerName': '',
                'eventDate': '',
                'eventTitle': '<div style="text-align:center">The EVE API is currently down</div>',
                'duration': 0,
                'isImportant': 0,
                'eventText': 'Fuck CCP tbqh imho srsly',
                'endsIn':-1,
                'forumLink': ''
            }]}
        
        events = []
        events_node_children = dom.getElementsByTagName('rowset')[0].childNodes
       
        for node in events_node_children:
            if node.nodeType == 1:
                ownerID = node.getAttribute('ownerID')                
                if ownerID != '1':
                    date = node.getAttribute('eventDate')                
                    dt = datetime.strptime(date,'%Y-%m-%d %H:%M:%S')                
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
                            'eventID': node.getAttribute('eventID'),
                            'ownerName': node.getAttribute('ownerName'),
                            'eventDate': date,
                            'eventTitle': node.getAttribute('eventTitle'),
                            'duration': duration,
                            'isImportant': node.getAttribute('importance'),
                            'eventText': node.getAttribute('eventText'),
                            'endsIn':endsIn,
                            'forumLink': forumlink
                        }                
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
                'forumLink': ''
            }]}
        else:
            return {'ops':events}

