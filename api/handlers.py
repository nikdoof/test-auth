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
                return rc.NOT_HERE
        elif 'user' in request.GET:
            try:
                u = User.objects.get(username=request.GET['user'])
            except User.DoesNotExist:
                return rc.NOT_HERE
        elif 'serviceuid' in request.GET:
            try:
                u = ServiceAccount.objects.get(service_uid=request.get['serviceuid']).user
            except ServiceAccount.DoesNotExist:
                return rc.NOT_HERE
        elif request.user:
            u = request.user

        chars = []
        for a in u.eveaccount_set.all():
            chars.append(a.characters.all())

        d = { 'id': u.id, 'username': u.username, 'email': u.email,
              'serviceaccounts': u.serviceaccount_set.all(), 'characters': chars,
              'groups': u.groups.all(), 'staff': u.is_staff, 'superuser': u.is_superuser }

        return d


class LoginHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, id=None):
        if id:
            try:
                u = User.objects.get(id=id)
            except (User.DoesNotExist, ValueError):
                return rc.NOT_HERE

        if request.GET.get('user', None):
            try:
                u = User.objects.get(username=request.GET['user'])
            except User.DoesNotExist:
                return rc.NOT_HERE

        d = { 'auth': 'ok', 'id': u.id, 'username': u.username,
              'email': u.email, 'groups': u.groups.all(),
              'staff': u.is_staff, 'superuser': u.is_superuser }

        if request.GET.get('pass', None) and request.GET['pass'] == u.password:
            return d

        return { 'auth': 'failed' }


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
            params[key] = value

        if request.GET.get('userid', None):
            obj = get_object_or_404(EVEAccount, pk=request.GET.get('userid', None))
            params['apikey'] = obj.api_key

        print params
        cached_doc = CachedDocument.objects.api_query(url_path, params, exceptions=False)

        return HttpResponse(cached_doc.body)
    
class OpTimerHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, id=None):
        obj = get_object_or_404(EVEAccount, user=FULL_API_USER_ID)
            
        params = {'userID':obj.id,'apiKey':obj.api_key,'characterID':FULL_API_CHARACTER_ID}
        
        cached_doc = CachedDocument.objects.api_query('/char/UpcomingCalendarEvents.xml.aspx', params, exceptions=False)
                
        dom = minidom.parseString(cached_doc.body.encode('utf-8'))
        enode = dom.getElementsByTagName('error')
        if enode:
            return {'error':True}
        
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
                    if startsIn < 0:
                        startsIn = 0              
                    event = {
                        'startsIn': startsIn,
                        'eventID': node.getAttribute('eventID'),
                        'ownerName': node.getAttribute('ownerName'),
                        'eventDate': date,
                        'eventTitle': node.getAttribute('eventTitle'),
                        'duration': node.getAttribute('duration'),
                        'isImportant': node.getAttribute('importance'),
                        'eventText': node.getAttribute('eventText')
                    }                
                    events.append(event)
        
        return {'ops':events}

