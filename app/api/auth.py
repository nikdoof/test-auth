from django.http import HttpResponseForbidden
from django.contrib.auth.models import AnonymousUser
from api.models import AuthAPIKey


class APIKeyAuthentication(object):

    def is_authenticated(self, request):

        params = {}
        for key, value in request.GET.items():
            params[key.lower()] = value

        if 'apikey' in params:
            try:
                keyobj = AuthAPIKey.objects.get(key=params['apikey'])
            except:
                keyobj = None

            if keyobj and keyobj.active:
                request.user = AnonymousUser()
                return True

        return False

    def challenge(self):
        return HttpResponseForbidden('Access Denied, use a API Key')
