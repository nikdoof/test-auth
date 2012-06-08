from urllib import urlencode
from datetime import datetime

from django.http import HttpResponseForbidden
from django.contrib.auth.models import AnonymousUser
from django.utils.timezone import now
from django.core.urlresolvers import resolve

from api.models import AuthAPIKey, AuthAPILog


class APIKeyAuthentication(object):
    """ Validats a request by API key passed as a GET parameter """

    def is_authenticated(self, request):
        try:
            keyobj = AuthAPIKey.objects.get(key=request.GET.get('apikey', None))
        except AuthAPIKey.DoesNotExist:
            return False
        else:
            if keyobj and keyobj.active:
                params = request.GET.copy()
                if params.get('apikey', None): del params['apikey']
                if len(params):
                    url = "%s?%s" % (request.path, urlencode(params))
                else:
                    url = request.path
                if not keyobj.permissions.filter(key=resolve(request.path).url_name).count():
                    return False
                AuthAPILog.objects.create(key=keyobj, access_datetime=now(), url=url)
                request.user = AnonymousUser()
                request.api_key = keyobj
                return True
        return False

    def challenge(self):
        return HttpResponseForbidden('Access Denied, use a valid API Key for this request.')
