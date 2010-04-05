from mumble.models import Mumble, MumbleUser
from sso.services import BaseService

import settings

class MumbleService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False, 
                 'use_corptag': True }

    def _get_server(self):
        return Mumble.objects.get(id=settings.MUMBLE_SERVER_ID)

    def add_user(self, username, password, **kwargs):
        """ Add a user, returns a UID for that user """

        if 'character' in kwargs and self.settings['use_corptag']:
            if kwargs['character'].corporation:
                if kwargs['character'].corporation.alliance:
                    tag = kwargs['character'].corporation.alliance.ticker
                else:
                    tag = kwargs['character'].corporation.ticker

        if tag:
            username = "[%s]%s" % (tag, username)

        return self.raw_add_user(username, password, user)

    def raw_add_user(username, password):
        mumbleuser = MumbleUser()
        mumbleuser.name = username
        mumbleuser.password = password
        mumbleuser.server = self._get_server()

        mumbleuser.save()
        return mumbleuser.name

    def check_user(self, username):
        """ Check if the username exists """
        try:
            mumbleuser = MumbleUser.objects.get(name=username, server=self._get_server())
        except MumbleUser.DoesNotExist:
            return False
        else:
            return True

    def delete_user(self, uid):
        """ Delete a user by uid """
        mumbleuser = MumbleUser.objects.get(name=uid, server=self._get_server())
        mumbleuser.delete()
        return True

    def disable_user(self, uid):
        """ Disable a user by uid """
        self.delete_user(uid)
        return True

    def enable_user(self, uid, password):
        """ Enable a user by uid """       
        if self.check_user(uid):
            mumbleuser = MumbleUser.objects.get(name=uid, server=self._get_server())
            mumbleuser.password = password
            mumbleuser.save()
        else:
            self.raw_add_user(uid, password)
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)

    def login(uid):
        """ Login the user and provide cookies back """ 
        pass


ServiceClass = 'MumbleService'
