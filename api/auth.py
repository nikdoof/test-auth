from django.http import HttpResponseForbidden
from django.contrib.auth.models import AnonymousUser
from api.models import AuthAPIKey

class APIKeyAuthentication(object):

    def is_authenticated(self, request):

        apikey = request.GET.get('apikey', None)
        if apikey:
            try:
                keyobj = AuthAPIKey.objects.get(key=apikey)
            except:
                keyobj = None

            if keyobj and keyobj.active:
                request.user = AnonymousUser()
                return True

        return False

    def challenge(self):
        return HttpResponseForbidden('Access Denied, use a API Key')

