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

from BeautifulSoup import BeautifulSoup
from piston.handler import BaseHandler
from piston.utils import rc, throttle
from gargoyle import gargoyle

from api.models import AuthAPIKey, AuthAPILog
from eve_proxy.models import CachedDocument
from eve_proxy.exceptions import *
from eve_api.app_defines import *
from eve_api.models import EVEAccount, EVEPlayerCharacter
from sso.models import ServiceAccount, Service
from hr.app_defines import *
from hr.models import Blacklist


class UserHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):
        if 'userid' in request.GET:
            try:
                u = User.objects.get(id=request.GET['userid'])
            except (User.DoesNotExist, ValueError):
                return {'auth': 'missing', 'missing': 'userid'}
        elif 'user' in request.GET:
            try:
                u = User.objects.get(username=request.GET['user'])
            except User.DoesNotExist:
                return {'auth': 'missing', 'missing': 'username'}
        elif 'serviceuid' in request.GET:
            try:
                u = ServiceAccount.objects.get(service_uid=request.GET['serviceuid']).user
            except ServiceAccount.DoesNotExist:
                return {'auth': 'missing', 'missing': 'ServiceAccount'}
        elif 'apiuserid' in request.GET:
            try:
                u = EVEAccount.objects.get(api_user_id=request.GET['apiuserid']).user
            except EVEAccount.DoesNotExist:
                return {'auth': 'missing', 'missing': 'apiuserid'}

        chars = []
        for a in u.eveaccount_set.all():
            chars.extend(a.characters.all())

        d = {'id': u.id, 'username': u.username, 'email': u.email,
             'serviceaccounts': u.serviceaccount_set.all(), 'characters': chars,
             'groups': u.groups.all(), 'staff': u.is_staff, 'superuser': u.is_superuser, 'redditaccounts': u.redditaccount_set.filter(validated=True) }

        return d


class LoginHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):

        u = None
        if request.GET.get('user', None):
            try:
                u = User.objects.get(username=request.GET['user'])
            except User.DoesNotExist:
                return {'auth': 'missing', 'missing': 'Username'}

        if u:
            if request.GET.get('pass', None) and u.is_active and request.GET['pass'] == u.get_profile().api_service_password:
                pchar = u.get_profile().primary_character
                if pchar:
                    pchardict = {'id': pchar.id,
                                 'name': pchar.name,
                                 'corporation': {'name': pchar.corporation.name, 'id': pchar.corporation.id, 'ticker': pchar.corporation.ticker },
                                }
                    if pchar.corporation.alliance:
                        pchardict['alliance'] = {'id': pchar.corporation.alliance.id, 'name': pchar.corporation.alliance.name, 'ticker': pchar.corporation.alliance.ticker }
                    else:
                        pchardict['alliance'] = None
                else:
                    pchardict = None
                return {'auth': 'ok', 'id': u.id, 'username': u.username,
                        'email': u.email, 'groups': u.groups.all().values('id', 'name'),
                        'staff': u.is_staff, 'superuser': u.is_superuser, 'primarycharacter': pchardict}
            else:
                return {'auth': 'failed'}

        return {'auth': 'missing', 'missing': 'all'}


class EveAPIHandler(BaseHandler):
    allowed_methods = ('GET')
    exclude = ('api_key')

    def read(self, request):

        s = None
        if request.GET.get('id', None):
            s = get_object_or_404(EVEAccount, pk=id)
        elif request.GET.get('userid', None):
            s = EVEAccount.objects.filter(user=request.GET['userid'])
        elif request.GET.get('corpid', None):
            s = EVEAccount.objects.filter(characters__corporation__id=request.GET['corpid'])
        elif request.GET.get('allianceid', None):
            s = EVEAccount.objects.filter(characters__corporation__alliance__id=request.GET['allianceid'])

        if s:
            return {'keys': s.values('api_user_id', 'user_id', 'api_status', 'api_last_updated')}

        return {'keys': []}


class EveAPIProxyHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):
        url_path = request.META['PATH_INFO'].replace(reverse('api-eveapiproxy'), "/")

        params = {}
        for key, value in request.GET.items():
            params[key.lower()] = value

        if 'userid' in params or 'keyid' in params:
            obj = get_object_or_404(EVEAccount, pk=params['userid'])

            # "Fix" new style keys
            if obj.api_keytype >= 3:
                params['keyid'] = params['userid']
                del params['userid']
                params['vcode'] = obj.api_key
            else:
                params['apikey'] = obj.api_key

        try:
            cached_doc = CachedDocument.objects.api_query(url_path, params, service=request.api_key.name)
        except DocumentRetrievalError, exc:
            return HttpResponse(exc, status=500)
        else:
            return HttpResponse(cached_doc.body)


class OpTimerHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, id=None):
        obj = get_object_or_404(EVEAccount, pk=settings.FULL_API_USER_ID)

        if gargoyle.is_active('eve-cak'):
            params = {'keyid': obj.pk, 'vcode': obj.api_key, 'characterID': settings.FULL_API_CHARACTER_ID}
        else:
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

        events = []
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
                            'eventText': ' '.join(BeautifulSoup(node.getAttribute('eventText')).findAll(text=True)),
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


class BlacklistHandler(BaseHandler):
    model = Blacklist
    allowed_methods = ('GET')
    fields = ('type', 'value', 'level', 'source', ('name', 'ticker'), 'created_date', 'expiry_date', 'reason')

    def read(self, request):
        if request.GET.get('value'):
            obj = Blacklist.objects.select_related('blacklistsource').filter(level__lte=BLACKLIST_LEVEL_ADVISORY,value__icontains=request.GET.get('value'))
            if obj.count() and request.GET.get('type'):
                obj = obj.filter(type=request.GET.get('type'))
        else:
            obj = []

        return obj


class CharacterHandler(BaseHandler):
    allowed_methods = ('GET')

    fields = ('id', 'name', ('corporation', ('id', 'name', ('alliance', ('id', 'name')))), 'corporation_date', 'balance', 'total_sp', 'security_status', 'director', 'skillset')

    @classmethod
    def skillset(cls, instance):
        return instance.eveplayercharacterskill_set.all().values('skill__id', 'skill__name', 'level', 'skillpoints')

    def read(self, request):
        s = []

        if request.GET.get('id', None):
            s = get_object_or_404(EVEPlayerCharacter, pk=id)
        elif request.GET.get('corpid', None):
            s = EVEPlayerCharacter.objects.filter(corporation__id=request.GET['corpid'])
        elif request.GET.get('allianceid', None):
            s = EVEPlayerCharacter.objects.filter(corporation__alliance__id=request.GET['allianceid'])
        return s

class AnnounceHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):

        sid = request.GET.get('sid', None)
        users = request.GET.getlist('users')
        groups = request.GET.getlist('groups')
        servers = request.GET.getlist('servers')
        message = request.GET.get('message', None)
        subject = request.GET.get('subject', None)

        if sid and to and message:
            srv = get_object_or_404(Service, pk=sid)

            if not srv.api == 'sso.services.jabber':
                return {'result': 'invalid'}

            api = srv.api_class
            return {'result': api.announce(api.settings['jabber_server'], message, subject, users=users, groups=groups, servers=servers) }

        return {'result': 'invalid'}


class EDKApiHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):

        alliance = request.GET.get('alliance', None)
        if not alliance:
            return {'auth': 'missing', 'missing': 'alliance'}

        objs = EVEAccount.objects.filter(characters__corporation__alliance=alliance, api_keytype=API_KEYTYPE_CORPORATION, api_status=API_STATUS_OK).extra(where=['(api_accessmask & 256) > 0'])
        return objs.values('api_user_id', 'api_key', 'characters__id', 'characters__name', 'characters__corporation__name')
