import re

from piston.handler import BaseHandler
from piston.utils import rc, throttle

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from eve_api.models import EVEAccount
from sso.models import ServiceAccount, Service

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
            d = { 'id': u.id, 'username': u.username, 'serviceaccounts': u.serviceaccount_set.all(), 'eveapi': u.eveaccount_set.all() }
            out.append (d)

        return out


class ServiceLoginHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):
        if not 'user' in request.GET or not 'pass' in request.GET or not 'service' in request.GET:
            return rc.BAD_REQUEST

        userobj = authenticate(username=request.GET['user'], password=request.GET['pass'])
        if userobj and userobj.is_active:
            try:
                serv = Service.objects.get(id=request.GET['service'])
            except:
                print 'bad service'
                return rc.BAD_REQUEST

            srvacct = userobj.serviceaccount_set.filter(service=serv)
            if len(srvacct):
                return { 'auth': 'ok', 'id': userobj.id, 'username': userobj.username, 'display-username': srvacct[0].service_uid, }

        return { 'auth': 'fail' }
