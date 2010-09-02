from sso.services import BaseService
from MumbleCtlIce import MumbleCtlIce
import Ice

class MumbleService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False, 
                 'mumble_server_id': 2,
                 'name_format': r'%(alliance)s - %(corporation)s - %(name)s',
                 'connection_string': 'Meta:tcp -h 127.0.0.1 -p 6502',
                 'ice_file': 'Murmur.ice' }

    def __init__(self):
        Ice.loadSlice(self.settings['ice_file'])
        import Murmur
        self.mur = Murmur

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

        if self.raw_add_user(username, kwargs['user'].email, password):
            self.update_groups(username, kwargs['user'].groups.all())
            return username
        else:
            return False

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

    def _create_groups(self, groups):
        """ Processes a list of groups and makes sure that related mumble groups exist """

        acls = self.mumblectl.getACL(self.settings['mumble_server_id'], 0)
        glist = []
        for mgroup in acls[1]:
            glist.append(mgroup.name)

        newgroups = False
        for agroup in groups:
            if not str(agroup.name.replace(' ', '').lower()) in glist:
                group = self.mur.Group()
                group.name = str(agroup.name.replace(' ', '').lower())
                group.members = []
                group.add = []
                group.remove = []
                group.inheritable = True
                group.inherit = True
                group.inherited = False
                acls[1].append(group)
                newgroups = True           

        if newgroups:
            self.mumblectl.setACL(self.settings['mumble_server_id'], 0, acls[0], acls[1], acls[2])

        return acls

    def update_groups(self, uid, groups):
        """ Update the UID's groups based on the provided list """
        
        # Get the User ID
        user = self.mumblectl.getRegisteredPlayers(self.settings['mumble_server_id'], uid).values()[0]
        if not user:
            return False

        acls = self._create_groups(groups)
        #acls = self.mumblectl.getACL(self.settings['mumble_server_id'], 0)

        for agroup in groups:
            gid = 0
            for mgroup in acls[1]:
                if mgroup.name == agroup.name.replace(' ', '').lower():
                    if not user['userid'] in acls[1][gid].members:
                        acls[1][gid].add.append(user['userid'])
                        acls[1][gid].members.append(user['userid'])
                else:
                    if user['userid'] in acls[1][gid].members:
                        acls[1][gid].remove.append(user['userid'])
                        acls[1][gid].remove.remove(user['userid'])
                gid = gid + 1

        self.mumblectl.setACL(self.settings['mumble_server_id'], 0, acls[0], acls[1], acls[2])      

ServiceClass = 'MumbleService'
