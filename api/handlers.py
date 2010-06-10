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
              'groups': u.groups.all() }

        return d

class LoginHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, id=None):
        if id:
            try:
                u = User.objects.get(id=id)
            except (User.DoesNotExist, ValueError):
                return rc.NOT_HERE

        if 'user' in request.GET:
            try:
                u = User.objects.get(username=request.GET['user'])
            except User.DoesNotExist:
                return rc.NOT_HERE

        d = { 'id': u.id, 'username': u.username, 'password': u.password, 'email': u.email, 'groups': u.groups.all() }
        return d

