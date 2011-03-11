import xmlrpclib
from sso.services import BaseService
import settings


class JabberService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False,
                 'use_auth_username': False,
                 'jabber_server': 'dredd.it',
                 'jabber_xmlrpc_url': 'http://127.0.0.1:4560',
                 'jabber_annouce_from': 'announcebot@pleaseignore.com'}

    def exec_xmlrpc(self, func, **kwargs):
        """ Send a XMLRPC request """
        if not hasattr(self, '_server'):
            self._server = xmlrpclib.Server(self.settings['jabber_xmlrpc_url'])
        params = {}
        for i in kwargs:
            params[i] = kwargs[i]

        return getattr(self._server, func)(params)

    def add_user(self, username, password, **kwargs):
        """ Add user to service """
        username = username.lower()
        res = self.exec_xmlrpc('register', user=username, host=self.settings['jabber_server'], password=password)
        if res['res'] == 0:
            if 'character' in kwargs:
                self.exec_xmlrpc('set_nickname', user=username, host=self.settings['jabber_server'], nickname=kwargs['character'].name)
                self.exec_xmlrpc('set_vcard2', user=username, host=self.settings['jabber_server'], name='ORG', subname='ORGNAME', content=kwargs['character'].corporation.name)
            uid = "%s@%s" % (username.lower(), self.settings['jabber_server'])
            if 'user' in kwargs:
                self.update_groups(uid, kwargs['user'].groups.all())
            return { 'username': uid, 'password': password }
        else:
            return False

    def delete_user(self, uid):
        """ Delete a user """
        username, server = uid.lower().split("@")

        for group in self.get_user_groups(uid):
            self.exec_xmlrpc('srg_user_del', user=username, host=server, group=group, grouphost=server)

        res = self.exec_xmlrpc('unregister', user=username, host=server)
        if res['res'] == 0:
            return True
        else:
            return False

    def check_user(self, username):
        """ Check if the username exists """
        if '@' in username:
            username, server = username.lower().split("@")
        else:
            server = self.settings['jabber_server']
        res = self.exec_xmlrpc('check_account', user=username, host=server)
        if res['res'] == 0:
            return True
        else:
            return False

    def disable_user(self, uid):
        """ Disable a user """
        username, server = uid.lower().split("@")
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
        username, server = uid.lower().split("@")
        res = self.exec_xmlrpc('change_password', user=username, host=server, newpass=password)
        if res['res'] == 0:
            return True
        else:
            return False

    def get_group_list(self, server):
        srvgrp = self.exec_xmlrpc('srg_list', host=server)
        return [grp['id'].lower() for grp in srvgrp['groups']]

    def get_group_members(self, server, group):
        members = self.exec_xmlrpc('srg_get_members', group=group, host=server)
        return [x['member'].lower() for x in members['members']]

    def get_user_groups(self, uid):
        grouplist = []
        username, server = uid.lower().split("@")
        for grp in self.get_group_list(server):
            if uid in self.get_group_members(server, grp):
                grouplist.append(grp)
        return grouplist

    def update_groups(self, uid, groups, character=None):
        username, server = uid.lower().split("@")

        current_groups = self.get_user_groups(uid)
        valid_groups = []

        for group in groups:
            groupname = group.name.lower().replace(' ', '-')
            self.exec_xmlrpc('srg_create', group=groupname, host=server, name=group.name, description='', display='')
            self.exec_xmlrpc('srg_user_add', user=username, host=server, group=groupname, grouphost=server)
            valid_groups.append(groupname)

        for group in (set(current_groups) - set(valid_groups)):
            self.exec_xmlrpc('srg_user_del', user=username, host=server, group=groupname, grouphost=server)

    def send_message(self, jid, msg):
        # send_stanza_c2s user host resource stanza
        username, server = jid.lower().split("@")
        self.exec_xmlrpc('send_stanza_c2s', user=username, host=server, resource='auth', stanza=str(msg))

    def announce(self, server, message, subject=None, all=False, users=[], groups=[]):
        import xmpp
        msg = xmpp.protocol.Message()
        msg.setFrom(self.settings['jabber_announce_from'])
        msg.setBody(message)
        if subject:
            msg.setSubject(subject)

        if all:
            msg.setTo('%s/announce/all-hosts/online' % server)
            self.send_message(self.settings['jabber_announce_from'], msg)
            return True
        else:
            if len(users):
                for u in set(users):
                    msg.setTo(u)
                    self.send_message(self.settings['jabber_announce_from'], msg)
                return True

            elif len(groups):
                tolist = []
                for g in groups:
                    tolist.extend([x for x in self.get_group_members(server, g)])
                    return self.announce(server, message, subject, users=tolist)
            else:
                return False

ServiceClass = 'JabberService'
