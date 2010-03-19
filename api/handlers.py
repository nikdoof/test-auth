import re

from piston.handler import BaseHandler
from piston.utils import rc, throttle

from django.contrib.auth.models import User
from eve_api.models import EVEAccount
from sso.models import ServiceAccount

class UserHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, id=None):
        if id:
            try:
                user = User.objects.filter(id=id)
            except (User.DoesNotExist, ValueError):
                return rc.NOT_HERE

        if 'user' in request.GET:
            try:
                user = User.objects.filter(username=request.GET['user'])
                print user
            except User.DoesNotExist:
                return rc.NOT_HERE

        if 'serviceuid' in request.GET:
            try:
                sa = ServiceAccount.objects.filter(service_uid=request.get['serviceuid'])
            except ServiceAccount.DoesNotExist:
                return rc.NOT_HERE
            user = sa.user


        out = []
        for u in user:
            sa = ServiceAccount.objects.filter(user=u)        
            ea = EVEAccount.objects.filter(user=u)

            d = { 'id': u.id, 'username': u.username, 'serviceaccounts': sa, 'eveapi': ea }
            out.append (d)

        return out	


class LoginHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):
        if request.user:
            return {'auth': 'notrequired', 'cookie': request.session.session_key }

        if not 'user' in request.GET or not 'pass' in request.GET:
            return rc.BAD_REQUEST

        if not user.is_active:
            return { 'auth': 'disabled' }

        if authenticate(user.name, password):
            login(request, user)
            return { 'auth': 'ok', 'id': user.id, 'username': user.username, 'cookie': request.session.session_key }
        else:
            return { 'auth': 'fail' }

class AccessHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):
        if not request.user:
            return rc.FORBIDDEN

        if not 'serviceid' in request.GET:
            return rc.BAD_REQUEST
        
        sa = ServiceAccount.objects.filter(user=request.user, service=request.GET['serviceid'])

        if sa:
            return { 'access': True, 'service': sa.service.id, 'service_uid': sa.service_uid }
        else:
            return { 'access': False }
