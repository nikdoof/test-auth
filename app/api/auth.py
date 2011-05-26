from datetime import datetime
from django.http import HttpResponseForbidden
from django.contrib.auth.models import AnonymousUser
from api.models import AuthAPIKey, AuthAPILog


class APIKeyAuthentication(object):
    """ Validats a request by API key passed as a GET parameter """

    def is_authenticated(self, request):
        try:
            keyobj = AuthAPIKey.objects.get(key=request.GET.get('apikey', None))
        except AuthAPIKey.DoesNotExist:
            pass
        else:
            if keyobj and keyobj.active:
                AuthAPILog(key=keyobj, access_datetime=datetime.utcnow(), url=request.get_full_path()).save()
                request.user = AnonymousUser()
                return True
        return False

    def challenge(self):
        return HttpResponseForbidden('Access Denied, use a API Key')
