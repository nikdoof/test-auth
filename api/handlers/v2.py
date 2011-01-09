from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from piston.handler import BaseHandler
from piston.utils import rc

class AuthenticationHandler(BaseHandler):
    """
    Authenticate a user against the Auth user DB.
    Provides back a session allowing further access
    """

    allowed_methods = ('GET')

    def read(self, request, username, password):

        user = get_object_or_404(User, username=username)
        if password and password == user.get_profile().api_service_password:
            return {'id': user.id, 'username': user.username,
                    'email': user.email, 'groups': user.groups.all(),
                    'staff': user.is_staff, 'superuser': user.is_superuser}

        resp = rc.FORBIDDEN
        resp.write({'auth': 'failed'})
        return resp
