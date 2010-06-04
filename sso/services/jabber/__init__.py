import xmlrpclib
from sso.services import BaseService
import settings


class JabberService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False,
                 'jabber_server': 'dredd.it',
                 'jabber_xmlrpc_url': 'http://127.0.0.1:4560' }

    def exec_xmlrpc(self, func, **kwargs):
        """ Send a XMLRPC request """
        server = xmlrpclib.Server(self.settings['jabber_xmlrpc_url'])
        params = {}
        for i in kwargs:
            params[i] = kwargs[i]

        return getattr(server, func)(params)

    def add_user(self, username, password, **kwargs):
        """ Add user to service """
        res = self.exec_xmlrpc('register', user=username, host=self.settings['jabber_server'], password=password)
        if res['res'] == 0:
            if 'character' in kwargs:
                self.exec_xmlrpc('set_nickname', user=username, host=self.settings['jabber_server'], nickname=kwargs['character'].name)
                self.exec_xmlrpc('set_vcard2', user=username, host=self.settings['jabber_server'], name='ORG', subname='ORGNAME', content=kwargs['character'].corporation.name)
            uid = "%s@%s" % (username, self.settings['jabber_server'])
            if 'user' in kwargs:
                self.update_groups(uid, kwargs['user'].groups.all())
            return uid
        else:
            return False

    def delete_user(self, uid):
        """ Delete a user """
        username, server = uid.split("@")

        for group in self.get_group_list(uid):
            self.exec_xmlrpc('srg_user_del', user=username, host=server, group=group, grouphost=server)

        res = self.exec_xmlrpc('unregister', user=username, host=server)
        if res['res'] == 0:
            return True
        else:
            return False

    def check_user(self, username):
        """ Check if the username exists """
        res = self.exec_xmlrpc('check_account', user=username, host=self.settings['jabber_server'])
        if res['res'] == 0:
            return True
        else:
            return False

    def disable_user(self, uid):
        """ Disable a user """
        username, server = uid.split("@")
        res = self.exec_xmlrpc('ban_account', host=server, user=username, reason='Auth account disable')
        if res['res'] == 0:
            return True
        else:
            return False

    def enable_user(self, uid, password):
        """ Enable a user """
        self.reset_password(uid, password)

    def reset_password(self, uid, password):
        """ Reset the user's password """
        username, server = uid.split("@")
        res = self.exec_xmlrpc('change_password', user=username, host=server, newpass=password)
        if res['res'] == 0:
            return True
        else:
            return False

    def get_group_list(self, uid):
        grouplist = []
        username, server = uid.split("@")
        srvgrp = self.exec_xmlrpc('srg_list', host=server)
        for grp in srvgrp['groups']:
            members = self.exec_xmlrpc('srg_get_members', group=grp['id'], host=server)
            members = map(lambda x: x['member'], members['members'])
            if uid in members:
                grouplist.append(grp['id'])

        return grouplist

    def update_groups(self, uid, groups):
        username, server = uid.split("@")

        current_groups = self.get_group_list(uid)
        valid_groups = []

        for group in groups:
            groupname = group.name.lower().replace(' ', '-')
            self.exec_xmlrpc('srg_create', group=groupname, host=server, name=group.name, description='', display='all')
            self.exec_xmlrpc('srg_user_add', user=username, host=server, group=groupname, grouphost=server)
            valid_groups.append(groupname)

        for group in (set(current_groups) - set(valid_groups)):
            self.exec_xmlrpc('srg_user_del', user=username, host=server, group=groupname, grouphost=server)

ServiceClass = 'JabberService'
