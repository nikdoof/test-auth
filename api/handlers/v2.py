from django.contrib.auth.models import User

from piston.handler import BaseHandler
from piston.utils import rc

from eve_api.models import EVEAccount
from eve_proxy.models import CachedDocument


class V2AuthenticationHandler(BaseHandler):
    """
    Authenticate a user against the Auth user DB.
    Provides back a session allowing further access
    """

    allowed_methods = ('GET')

    def read(self, request, username, password):
        """
        Validates login details for the provided user as
        long as 'username' and 'password' are provided.
        """

        try:
            user = User.object.get(username=username)
        except User.DoesNotExist:
            resp = rc.NOT_FOUND
            resp.write({'auth': 'notfound'})
            return resp

        if password and password == user.get_profile().api_service_password:
            return {'userid': user.id, 
                    'username': user.username,
                    'email': user.email,
                    'groups': user.groups.all().values_list('id', 'name'),
                    'staff': user.is_staff,
                    'superuser': user.is_superuser}

        resp = rc.FORBIDDEN
        resp.write({'auth': 'failed'})
        return resp


class V2EveAPIProxyHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request):
        url_path = request.META['PATH_INFO'].url_path.replace(reverse('v2-api-eveapiproxy'), "/")

        params = {}
        for key, value in request.GET.items():
            params[key.lower()] = value

        try:
            userid = request.GET.get('userid', None)
            obj = EVEAccount.objects.get(api_user_id=userid)
            params['apikey'] = obj.api_key
        except EVEAccount.DoesNotExist:
            pass

        try:
            cached_doc = CachedDocument.objects.api_query(url_path, params)
        except DocumentRetrievalError:
            return HttpResponse(status=500)
        else:
            return HttpResponse(cached_doc.body)
