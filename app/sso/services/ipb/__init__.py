import xmlrpclib
from sso.services import BaseService
import settings
from hashlib import md5

class IPBService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False,
                 'use_auth_username': True,
                 'ipb_display_name': "[%(corp)s] - %(name)s",
                 'ipb_endpoint': 'http://ipb.pleaseignore.com/interface/board/index.php',
                 'ipb_api_key': '51242ecca069b986106f04db1047cfc4',
                 'ipb_api_module': 'ipb' }

    def exec_xmlrpc(self, func, **kwargs):
        """ Send a XMLRPC request """
        if not hasattr(self, '_server'):
            self._server = xmlrpclib.Server(self.settings['ipb_endpoint'], verbose=True)
        params = {}
        for i in kwargs:
            params[i] = kwargs[i]
        params['api_key'] = self.settings['ipb_api_key']
        params['api_module'] = self.settings['ipb_api_module']

        return getattr(self._server, func)(params)

    def _create_group(self, name):
        """ Creates a IPB membergroup """
        ret = self.exec_xmlrpc('createGroup', group_name=name)
        if ret:
            return {'name': name, 'id': ret['changeSuccessful']}

    def add_user(self, username, password, **kwargs):
        """ Add user to service """

        password = md5(password).hexdigest()
        details = { 'name': kwargs['character'].name,
                    'alli': kwargs['character'].corporation.alliance.ticker,
                    'corp': kwargs['character'].corporation.ticker }
        display = self.settings['ipb_display_name'] % details
        ret = self.exec_xmlrpc('createUser', username=username, email=kwargs['user'].email, display_name=display, password=password)

        return username

    def delete_user(self, uid):
        """ Delete a user """
        pass

    def check_user(self, username):
        """ Check if the username exists """
        ret = self.exec_xmlrpc('fetchMember', search_type='email', search_string=username)
        return ret

    def disable_user(self, uid):
        """ Disable a user """
        pass

    def enable_user(self, uid, password):
        """ Enable a user """
        pass

    def reset_password(self, uid, password):
        """ Reset the user's password """
        pass

    def update_groups(self, uid, groups, character=None):

        user_id = self.check_user(uid)

        # Get all IPB groups

        # Iterate through the provided group list and create any missing ones
        grplist = []
        for g in groups:
            if not g.name in grplist:
                ret = self._create_group(g.name)
                if ret:
                    grplist[ret['name']] = ret['id']

        # Assign each group to the user id
        for gk in grplist:
            self.exec_xmlrpc('updateUserGroup', user_id=user_id, group_name=gk, action='ADD')

ServiceClass = 'IPBService'
