import urllib
from sso.services import BaseService
from ts3 import TS3Server

class TS3Service(BaseService):

    settings = { 'require_user': True,
                 'require_password': False,
                 'provide_login': False,
                 'host': 'mumble.pleaseignore.com',
                 'port': 10011,
                 'sa_login': 'serveradmin',
                 'sa_password': '',
                 'vhost_id': 0,
                 'authed_sgid': 12,
                 'name_format': '%(alliance)s - %(corporation)s - %(name)s',
                 'bookmark_name': 'TEST Alliance TS3'}

    def __init__(self):
        pass

    @property
    def conn(self):
        if not hasattr(self, '_conn'):
            self._conn = TS3Server(self.settings['host'], self.settings['port'])
            self._conn.login(self.settings['sa_login'], self.settings['sa_password'])
            self._conn.use(self.settings['vhost_id'])
            
        return self._conn

    def add_user(self, username, password, **kwargs):
        """ Add a user, returns a UID for that user """

        details = { 'name': username,
                    'alliance': kwargs['character'].corporation.alliance.ticker,
                    'corporation': kwargs['character'].corporation.ticker }

        self._create_groups(kwargs['user'].groups.all().values_list('name', flat=True))
        username = self.settings['name_format'] % details
        ret = self.conn.send_command('tokenadd', {'tokentype': 0, 'tokenid1': self.settings['authed_sgid'], 'tokenid2': 0, 'tokendescription': kwargs['character'].name.replace(' ', ''), 'tokencustomset': "ident=sso_uid value=%s|ident=sso_userid value=%s|ident=eve_charid value=%s" % (kwargs['character'].name.replace(' ', ''), kwargs['user'].id, kwargs['character'].id) })
        if 'keys' in ret and 'token' in ret['keys']:
            token = ret['keys']['token']
            url = "<a href='ts3server://%s?token=%s'>Click this link to connect and register on TS3</a>" % (self.settings['host'], token)
            return { 'username': kwargs['character'].name.replace(' ', ''), 'display name': username, 'permission token': token, 'registration url': url }

        return None

    def check_user(self, uid):
        """ Check if the username exists """
        # Lookup user using customsearch with sso_uid=uid
        return self._get_userid(uid)

    def delete_user(self, uid):
        """ Delete a user by uid """
        user = self._get_userid(uid)
        if user:

            for client in self.conn.send_command('clientlist'):
                if client['keys']['client_database_id'] == user:
                    self.conn.send_command('clientkick', {'clid': client['keys']['clid'], 'reasonid': 5, 'reasonmsg': 'Auth service deleted'})

            ret = self.conn.send_command('clientdbdelete', {'cldbid': user })
        return True

    def disable_user(self, uid):
        """ Disable a user by uid """
        user = self._get_userid(uid)
        if user:
            ret = self.conn.send_command('servergroupdelclient', {'sgid': self.settings['authed_sgid'], 'cldbid': user })
        return True

    def enable_user(self, uid, password):
        """ Enable a user by uid """

        user = self._get_userid(uid)
        if user:
            ret = self.conn.send_command('servergroupaddclient', {'sgid': self.settings['authed_sgid'], 'cldbid': user })
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        pass

    def login(uid):
        """ Login the user and provide cookies back """ 
        pass

    def _group_by_name(self, groupname):
        if not hasattr(self, '__group_cache') or not self.__group_cache:
            self.__group_cache = self.conn.send_command('servergrouplist')
        for group in self.__group_cache:
            if group['keys']['name'] == groupname:
                return group['keys']['sgid']

        return None

    def _get_userid(self, uid):
        """ Finds the TS3 ID of a user from their UID """

        ret = self.conn.send_command('customsearch', {'ident': 'sso_uid', 'pattern': uid})
        if ret and 'keys' in ret and 'cldbid' in ret['keys']:
            return ret['keys']['cldbid']

    def _create_group(self, groupname):
        """ Creates a Server Group and returns the SGID """
        sgid = self._group_by_name(groupname)
        if not sgid:
            ret = self.conn.send_command('servergroupadd', { 'name': groupname })
            self.__group_cache = None
            sgid = ret['keys']['sgid']
            self.conn.send_command('servergroupaddperm', { 'sgid': sgid, 'permsid': 'i_group_needed_modify_power', 'permvalue': 75, 'permnegated': 0, 'permskip': 0 })
        return sgid

    def _create_groups(self, groups):
        """ Creates groups from a list """
        output = []
        for g in groups:
            output.append(self._create_group(g))
        return output

    def update_groups(self, uid, groups):
        """ Update the UID's groups based on the provided list """

        cldbid = self._get_userid(uid)

        if cldbid:
            tsglist = self.conn.send_command('servergroupsbyclientid', {'cldbid': cldbid })
            donelist = []
            if type(tsglist) == type(list()):
                for g in tsglist:
                    donelist.append(g['keys']['sgid'])
            else:
                donelist.append(tsglist['keys']['sgid'])

            if groups.count():
                addgroups = self._create_groups(groups.values_list('name', flat=True))
                for g in addgroups:
                    if not g in donelist:
                        ret = self.conn.send_command('servergroupaddclient', {'sgid': g, 'cldbid': cldbid })

                #remv = set(donelist) - set(addgroups)
                #if int(self.settings['authed_sgid']) in remv:
                #     ret = self.conn.send_command('servergroupdelclient', {'sgid': g, 'cldbid': cldbid })
        return True

ServiceClass = 'TS3Service'
