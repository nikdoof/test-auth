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
                 'name_format': '%(alliance)s - %(corporation)s - %(name)s'}

    def __init__(self):
        pass

    @property
    def _conn(self):
        if not hasattr(self, '__conn'):
            self.__conn = TS3Server(self.settings['host'], self.settings['port'])
            self.__conn.login(self.settings['sa_login'], self.settings['sa_password'])
            self.__conn.use(self.settings['vhost_id'])
            
        return self.__conn

    def add_user(self, username, password, **kwargs):
        """ Add a user, returns a UID for that user """

        details = { 'name': username,
                    'alliance': kwargs['character'].corporation.alliance.ticker,
                    'corporation': kwargs['character'].corporation.ticker }

        username = self.settings['name_format'] % details
        ret = self._conn.send_command('tokenadd', {'tokentype': 0, 'tokenid1': self.settings['authed_sgid'], 'tokenid2': 0, 'tokendescription': "Auth Token for %s" % username, 'tokencustomset': "ident=sso_uid value=%s" % username })

        if 'keys' in ret and 'token' in ret['keys']:
            token = ret['keys']['token']
            url = "<a href='ts3server://%s?%s/'>Register</a>" % (self.settings['host'], urllib.urlencode({'nickname': username, 'addbookmark': 'TEST Alliance TS3', 'token': token}))
            return { 'username': username, 'permission token': token, 'registration url': url }

        return None

    def check_user(self, uid):
        """ Check if the username exists """
        # Lookup user using customsearch with sso_uid=uid
        return self._get_userid(uid)

    def delete_user(self, uid):
        """ Delete a user by uid """
        user = self._get_userid(uid)
        if user:
            ret = self._conn.send_command('clientdbdelete', {'cldbid': user })
        return True

    def disable_user(self, uid):
        """ Disable a user by uid """
        user = self._get_userid(uid)
        if user:
            ret = self._conn.send_command('servergroupdelclient', {'sgid': self.settings['authed_sgid'], 'cldbid': user })
        return True

    def enable_user(self, uid, password):
        """ Enable a user by uid """

        user = self._get_userid(uid)
        if user:
            ret = self._conn.send_command('servergroupaddclient', {'sgid': self.settings['authed_sgid'], 'cldbid': user })
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        pass

    def login(uid):
        """ Login the user and provide cookies back """ 
        pass

    def _get_userid(self, uid):
        """ Finds the TS3 ID of a user from their UID """

        ret = self._conn.send_command('customsearch', {'ident': 'sso_uid', 'pattern': 'uid'})
        if ret and type(ret) == type(list):
            return ret[0]['cldbid']

    def _create_groups(self, groups):
        agroups = groups.values_list('name')
        ngroups = agroups.copy()
        for tsg in self._conn.send_command('servergrouplist'):
                ngroups.remove(tsg['keys']['name'])

        if len(ngroups):
            for g in ngroups:
                self._conn.send_command('servergroupadd', { 'name': g })

        ret = []
        for tsg in self._conn.send_command('servergrouplist'):
            if tsg['keys']['name'] in agroups:
                ret.append(tsg['keys'])
        return ret

    def update_groups(self, uid, groups):
        """ Update the UID's groups based on the provided list """

        if groups.count():
            addgroups = self._create_groups(groups)          
            user = self._get_userid(uid)
            for g in addgroups:
                ret = self._conn.send_command('servergroupaddclient', {'sgid': g['sgid'], 'cldbid': user })

ServiceClass = 'TS3Service'
