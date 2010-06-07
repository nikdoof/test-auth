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
                u = User.objects.filter(id=id)
            except (User.DoesNotExist, ValueError):
                return rc.NOT_HERE

        if 'user' in request.GET:
            try:
                u = User.objects.filter(username=request.GET['user'])
            except User.DoesNotExist:
                return rc.NOT_HERE

        if 'serviceuid' in request.GET:
            try:
                sa = ServiceAccount.objects.filter(service_uid=request.get['serviceuid'])
            except ServiceAccount.DoesNotExist:
                return rc.NOT_HERE
            u = sa.user


        d = { 'id': u.id, 'username': u.username, 'password': u.password, 'serviceaccounts': u.serviceaccount_set.all(), 
                  'eveapi': u.eveaccount_set.all(), 'email': u.email }
        return d


class ServiceLoginHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):
        if not 'user' in request.GET or not 'pass' in request.GET:
            return rc.BAD_REQUEST

        userobj = authenticate(username=request.GET['user'], password=request.GET['pass'])
        if userobj and userobj.is_active:

            if 'service' in request.GET:
                try:
                    serv = Service.objects.get(id=request.GET['service'])
                except:
                    return rc.BAD_REQUEST

                srvacct = userobj.serviceaccount_set.filter(service=serv)
                if len(srvacct):
                    displayname = srvacct[0].service_uid
                else:
                    displayname = userobj.username
            else:
                displayname = userobj.username


            return { 'auth': 'ok', 'id': userobj.id, 'username': userobj.username, 'email': userobj.email,
                     'display-username': displayname, 'eveapi': userobj.eveaccount_set.all() }

        return { 'auth': 'fail' }
