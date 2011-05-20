from django.contrib.auth.models import User

from piston.handler import BaseHandler
from piston.utils import rc

from eve_api.models import EVEAccount, EVEPlayerCharacter
from eve_proxy.models import CachedDocument


class V2AuthenticationHandler(BaseHandler):
    """
    Authenticate a user against the Auth user DB.
    Provides back a session allowing further access
    """

    allowed_methods = ('GET')

    def read(self, request):
        """
        Validates login details for the provided user as
        long as 'username' and 'password' are provided.
        """

        username = request.GET.get('username', None)
        password = request.GET.get('password', None)

        if not username or not password:
            return rc.BAD_REQUEST

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
                    'groups': user.groups.all().values('id', 'name'),
                    'staff': user.is_staff,
                    'superuser': user.is_superuser}

        resp = rc.FORBIDDEN
        resp.write({'auth': 'failed'})
        return resp


class V2EveAPIProxyHandler(BaseHandler):
    """
    Provides a proxy handler to the EVE API using 'eve_proxy'
    """

    allowed_methods = ('GET')

    def read(self, request):
        """
        Acts as a EVE API proxy, all params are passed to the
        API, for the exception of 'apikey' which is dervived from the
        stored information and 'userid'

        'apikey' field should be populated with the Auth API key.
        """
        url_path = request.META['PATH_INFO'].url_path.replace(reverse('v2-api-eveapiproxy'), "/")

        params = {}
        for key, value in request.GET.items():
            params[key.lower()] = value

        try:
            obj = EVEAccount.objects.get(pk=request.GET.get('userid', None))
            params['apikey'] = obj.api_key
        except EVEAccount.DoesNotExist:
            resp = rc.NOT_FOUND
            resp.write({'user': 'notfound'})
            return resp

        try:
            cached_doc = CachedDocument.objects.api_query(url_path, params)
        except DocumentRetrievalError:
            return HttpResponse(status=500)
        else:
            return HttpResponse(cached_doc.body)


class V2UserHandler(BaseHandler):
    allowed_methods = ('GET')

    def read(self, request, userid):
        try:
            u = User.objects.get(id=userid)
        except (User.DoesNotExist, ValueError):
            resp = rc.NOT_FOUND

        charlist = []
        for acc in u.eveaccount_set.all():
            for char in acc.characters.all().select_related('characters').values('id', 'name', 'corporation', 'corporation_date', 'corporation__name'):
                d = dict(char)
                d['eveaccount'] = acc.pk
                charlist.append(d)

        d = {'id': u.id,
             'username': u.username,
             'email': u.email,
             'eveaccounts': u.eveaccount_set.all().values('api_user_id', 'description', 'api_status', 'api_keytype'),
             'serviceaccounts': u.serviceaccount_set.all().values('service', 'service__name', 'service__api', 'service_uid'),
             'characters': charlist,
             'groups': u.groups.all().values('id', 'name'),
             'staff': u.is_staff,
             'superuser': u.is_superuser}

        return d

