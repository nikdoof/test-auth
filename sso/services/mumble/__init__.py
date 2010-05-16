from mumble.models import Mumble, MumbleUser
from sso.services import BaseService

class MumbleService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False, 
                 'mumble_server_id': 1,
                 'name_format': r'%(alliance}s | %(corporation)s | %(name)s' }

    def _get_server(self):
        return Mumble.objects.get(id=self.settings['mumble_server_id'])

    def add_user(self, username, password, **kwargs):
        """ Add a user, returns a UID for that user """

        details = { 'name': username,
                    'alliance': kwargs['character'].corporation.alliance.ticker,
                    'corporation': kwargs['character'].corporation.ticker }

        username = self.settings['name_format'] % details

        return self.raw_add_user(username, password)

    def raw_add_user(self, username, password):
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
        try:
            mumbleuser = MumbleUser.objects.get(name=uid, server=self._get_server())
        except MumbleUser.DoesNotExist:
            return True
        try:
            mumbleuser.delete()
        except:
            pass
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
