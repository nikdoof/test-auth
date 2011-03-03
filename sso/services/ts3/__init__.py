import urllib
from sso.services import BaseService
from ts3 import TS3Server

class TS3Service(BaseService):

    settings = { 'require_user': True,
                 'require_password': False,
                 'provide_login': False,
                 'use_auth_username': False,
                 'host': 'mumble.pleaseignore.com',
                 'port': 10011,
                 'sa_login': 'serveradmin',
                 'sa_password': '',
                 'vhost_id': 0,
                 'authed_sgid': 12,
                 'name_format': '%(alliance)s - %(corporation)s - %(name)s',
                 'bookmark_name': 'TEST Alliance TS3',
                 'ignore_groups': [6]}

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
                    'corporation': kwargs['character'].corporation.ticker }

        if kwargs['character'].corporation.alliance:
            details['alliance'] = kwargs['character'].corporation.alliance.ticker
        else:
            details['alliance'] = None

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
            if ret == '0':
                return True
        else:
            return True

    def disable_user(self, uid):
        """ Disable a user by uid """
        user = self._get_userid(uid)
        if user:
            ret = self.conn.send_command('servergroupdelclient', {'sgid': self.settings['authed_sgid'], 'cldbid': user })
            if ret == '0':

                groups = self._user_group_list(user)
                for group in groups:
                    self.conn.send_command('servergroupdelclient', {'sgid': groups[group], 'cldbid': user })

                return True
        return False

    def enable_user(self, uid, password):
        """ Enable a user by uid """

        user = self._get_userid(uid)
        if user:
            ret = self.conn.send_command('servergroupaddclient', {'sgid': self.settings['authed_sgid'], 'cldbid': user })
            if ret == '0':
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
            self.conn.send_command('servergroupaddperm', { 'sgid': sgid, 'permsid': 'i_group_needed_member_add_power', 'permvalue': 100, 'permnegated': 0, 'permskip': 0 })
            self.conn.send_command('servergroupaddperm', { 'sgid': sgid, 'permsid': 'i_group_needed_member_remove_power', 'permvalue': 100, 'permnegated': 0, 'permskip': 0 })
        return sgid

    def _group_list(self):
        """ List of all groups on the TS server """

        if not hasattr(self, '__group_cache') or not self.__group_cache:
            self.__group_cache = self.conn.send_command('servergrouplist')
        outlist = {}
        for group in self.__group_cache:
            outlist[group['keys']['name']] = group['keys']['sgid']
        return outlist

    def _user_group_list(self, cldbid):
        """ List of all groups assigned to a user """

        groups = self.conn.send_command('servergroupsbyclientid', {'cldbid': cldbid })
        outlist = {}

        if type(groups) == list:
            for group in groups:
                outlist[group['keys']['name']] = group['keys']['sgid']
        elif type(groups) == dict:
            outlist[groups['keys']['name']] = groups['keys']['sgid']

        return outlist

    def update_groups(self, uid, groups, character=None):
        """ Update the UID's groups based on the provided list """

        cldbid = self._get_userid(uid)

        if cldbid:
            tsgrplist = self._group_list()
            usrgrplist = self._user_group_list(cldbid)

            # Add groups
            if groups.count():
                for g in groups:
                    if not g.name in tsgrplist:
                        tsgrplist[g.name] = self._create_group(g.name)
                    if not g.name in usrgrplist:
                        self.conn.send_command('servergroupaddclient', {'sgid': tsgrplist[g.name], 'cldbid': cldbid })
                        usrgrplist[g.name] = tsgrplist[g.name]

            # Add to corporation groups
            if character and character.corporation:
                if character.corporation.ticker in usrgrplist:
                    del usrgrplist[character.corporation.ticker]
                else:
                    if not character.corporation.ticker in tsgrplist:
                        tsgrplist[character.corporation.ticker] = self._create_group(character.corporation.ticker)
                    self.conn.send_command('servergroupaddclient', {'sgid': tsgrplist[character.corporation.ticker], 'cldbid': cldbid })

            # Remove OKed groups from the delete list
            for g in groups:
                if g.name in usrgrplist:
                    del usrgrplist[g.name]

            # Remove ignored and admin groups
            for k, v in usrgrplist.items():
                if not int(v) == self.settings['authed_sgid'] and not int(v) in self.settings['ignore_groups']:
                    self.conn.send_command('servergroupdelclient', {'sgid': v, 'cldbid': cldbid })

        return True

ServiceClass = 'TS3Service'
