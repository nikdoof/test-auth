from mumble.models import Mumble, MumbleUser
from sso.services import BaseService

import settings

class MumbleService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False }

    def _get_server(self):
        return Mumble.objects.get(id=settings.MUMBLE_SERVER_ID)

    def add_user(self, username, password):
        """ Add a user, returns a UID for that user """
        mumbleuser = MumbleUser()
        mumbleuser.name = username
        mumbleuser.password = password
        mumbleuser.server = self._get_server()
        mumbleuser.save()
        return mumbleuser.name

    def check_user(self, username):
        """ Check if the username exists """
        try:
            mumbleuser = MumbleUser.objects.get(name=username)
        except MumbleUser.DoesNotExist:
            return False
        else:
            return True

    def delete_user(self, uid):
        """ Delete a user by uid """
        mumbleuser = MumbleUser.objects.get(name=uid)
        mumbleuser.delete()

    def disable_user(self, uid):
        """ Disable a user by uid """
        pass

    def enable_user(self, uid, password):
        """ Enable a user by uid """       
        pass

    def login(uid):
        """ Login the user and provide cookies back """ 
        pass


ServiceClass = 'MumbleService'
