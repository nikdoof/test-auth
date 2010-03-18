import re

from piston.handler import BaseHandler
from piston.utils import rc, throttle

from django.contrib.auth.models import User
from sso.models import ServiceAccount

class UserHandler(BaseHandler):
    allowed_methods = ('GET')
    fields = ('id', 'username', 'password' )
    model = User

    def read(self, request, user=None, id=None, sid=None, suid=None):

        if user:
            try:
                user = User.objects.get(username=user)
            except User.DoesNotExist:
                return rc.NOT_HERE
        if id:
            try:
                user = User.objects.get(id=id)
            except (User.DoesNotExist, ValueError):
                return rc.NOT_HERE
        if sid:
            try:
                sa = ServiceAccount.objects.get(service_id=sid, service_uid=suid)
            except ServiceAccount.DoesNotExist:
                return rc.NOT_HERE
            user = sa.user

        enctype, salt, passwd = user.password.split("$")
        return { 'id': user.id, 'username': user.username, 'type': enctype, 'salt': salt }


class LoginHandler(BaseHandler):
    allowed_methods = ('GET')
    fields = ('id', 'username', 'password' )
    model = User

    def read(self, request):
        if 'hash' not in request.GET:
            return rc.BAD_REQUEST
        else:
            hash = request.GET['hash']

        if 'username' in request.GET:
            try:
                user = User.objects.get(username=request.GET['username'])
            except (User.DoesNotExist, ValueError):
                return rc.NOT_HERE
        elif 'id' in request.GET:
            try:
                user = User.objects.get(id=request.GET['id'])
            except (User.DoesNotExist, ValueError):
                return rc.NOT_HERE
        elif 'suid' in request.GET:
            if 'sid' not in request.GET:
                return rc.BAD_REQUEST
            try:
                sa = ServiceAccount.objects.get(service_uid=request.GET['suid'], service=request.GET['sid'])
                user = sa.user
            except (ServiceAccount.DoesNotExist, ValueError):
                return rc.NOT_HERE
        else:
            return rc.BAD_REQUEST

        enctype, salt, passwd = user.password.split("$")

        if hash == passwd:
            return { 'auth': 'ok', 'id': user.id, 'username': user.username }
        else:
            return { 'auth': 'fail' }


class ServiceAccountHandler(BaseHandler):    
    allowed_methods = ('GET')
    fields = ('id', 'user_id', 'service_uid' )
    model = ServiceAccount

    def read(self, request, id=None):
        if id:
            try:
                account = ServiceAccount.objects.get(id=id)
            except (ServiceAccount.DoesNotExist, ValueError):
                return rc.NOT_HERE
        else:
            if request.GET['serviceuid']:
                try:
                    account = ServiceAccount.objects.get(service_uid=request.GET['serviceuid'])
                except (ServiceAccount.DoesNotExist, ValueError):
                    return rc.NOT_HERE

        return account

