from sso.services import BaseService
from MumbleCtlIce import MumbleCtlIce

class MumbleService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False, 
                 'mumble_server_id': 2,
                 'name_format': r'%(alliance)s - %(corporation)s - %(name)s',
                 'connection_string': 'Meta:tcp -h 127.0.0.1 -p 6502',
                 'ice_file': 'Murmur.ice' }

    @property
    def mumblectl(self):
        if not hasattr(self, '_mumblectl'):
            self._mumblectl = MumbleCtlIce(self.settings['connection_string'], self.settings['ice_file'])
        return self._mumblectl

    def add_user(self, username, password, **kwargs):
        """ Add a user, returns a UID for that user """

        details = { 'name': username,
                    'alliance': kwargs['character'].corporation.alliance.ticker,
                    'corporation': kwargs['character'].corporation.ticker }

        username = self.settings['name_format'] % details

        return self.raw_add_user(username, kwargs['user'].email, password)

    def raw_add_user(self, username, email, password):
        if self.mumblectl.registerPlayer(self.settings['mumble_server_id'], username, email, password):
            return username

        return False

    def check_user(self, username):
        """ Check if the username exists """
        if len(self.mumblectl.getRegisteredPlayers(self.settings['mumble_server_id'], username)):
            return True
        else:
            return False

    def delete_user(self, uid):
        """ Delete a user by uid """
        ids = self.mumblectl.getRegisteredPlayers(self.settings['mumble_server_id'], uid)
        if len(ids) > 0:
            for accid in ids:
                acc = ids[accid]
                self.mumblectl.unregisterPlayer(self.settings['mumble_server_id'], acc['userid'])

        return True

    def disable_user(self, uid):
        """ Disable a user by uid """
        self.delete_user(uid)
        return True

    def enable_user(self, uid, password):
        """ Enable a user by uid """       
        ids = self.mumblectl.getRegisteredPlayers(self.settings['mumble_server_id'], uid)
        if len(ids) > 0:
            for accid in ids:
                acc = ids[accid]
                self.mumblectl.setRegistration(self.settings['mumble_server_id'], acc['userid'], acc['name'], acc['email'], password)
            return True
        else:
            if self.raw_add_user(uid, '', password):
                return True

    def set_user(self, uid, name = ''):
        """ Set values ona user by uid """       
        ids = self.mumblectl.getRegisteredPlayers(self.settings['mumble_server_id'], uid)
        if len(ids) > 0:
            for accid in ids:
                acc = ids[accid]
                self.mumblectl.setRegistration(self.settings['mumble_server_id'], acc['userid'], name, acc['email'], acc['pw'])
            return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)

    def login(uid):
        """ Login the user and provide cookies back """ 
        pass


ServiceClass = 'MumbleService'
