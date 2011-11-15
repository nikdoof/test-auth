import xmpp
import urllib, urllib2
import xmlrpclib
from sso.services import BaseService
from django.conf import settings


class JabberService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False,
                 'use_auth_username': False,
                 'jabber_server': 'dredd.it',
                 'jabber_xmlrpc_url': 'http://127.0.0.1:4560',
                 'jabber_announce_from': 'announcebot@pleaseignore.com',
                 'jabber_announce_password': 'pepperllama',
                 'jabber_announce_endpoint': 'http://127.0.0.1:5281/message',
                 'jabber_announce_servers': ['pleaseignore.com'] }

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
            if not group.name in current_groups:
                groupname = group.name.lower().replace(' ', '-').replace('.', '')
                self.exec_xmlrpc('srg_create', group=groupname, host=server, name=group.name, description='', display='')
                self.exec_xmlrpc('srg_user_add', user=username, host=server, group=groupname, grouphost=server)
                if not groupname in current_groups: current_groups.append(groupname)
            if not groupname in valid_groups: valid_groups.append(groupname)

        for group in (set(current_groups) - set(valid_groups)):
            self.exec_xmlrpc('srg_user_del', user=username, host=server, group=group, grouphost=server)

    @property
    def authhandler(self):
        """ Generates the urllib2 Auth Handler for authenticated requests """
        if not hasattr(self, '_authhandler'):
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(None, self.settings['jabber_announce_endpoint'], self.settings['jabber_announce_from'], self.settings['jabber_announce_password'])
            self._authhandler = urllib2.HTTPBasicAuthHandler(passman)
        return self._authhandler

    def send_message(self, jid, body, subject=None, msgfrom=None):

        msg = xmpp.protocol.Message()
        if len(jid) > 1:
            msg.setTo('multicast')
            multi = msg.addChild(name='addresses', namespace='http://jabber.org/protocol/address')
            for j in jid:
                multi.addChild(name='address', attrs={'jid': j, 'type': 'bcc'})
        elif len(jid) == 1:
            msg.setTo(jid[0])
        else:
            return False

        if msgfrom:
            msg.setFrom(msgfrom)
        else:
            msg.setFrom(self.settings['jabber_announce_from'])
        msg.setType('chat')
        if subject:
            msg.setSubject(subject)
        msg.setBody(body)

        print str(msg)

        opener = urllib2.build_opener(self.authhandler)
        req = urllib2.Request(self.settings['jabber_announce_endpoint'], str(msg))
        resp = opener.open(req)

        return resp.read().strip()[:2] == 'OK'

    def announce(self, server, message, subject=None, users=[], groups=[]):

        if 'all' in groups:
            dest = ['%s/announce/online' % server for server in self.settings['jabber_announce_servers']]
        else:
            dest = []

            if len(users):
                for u in set(users):
                    dest.append(u)

            elif len(groups):
                for g in groups:
                    dest.extend([x for x in self.get_group_members(server, g)])

            dest = set(dest)

        if len(dest):
            return self.send_message(dest, message, subject)
        return False

ServiceClass = 'JabberService'
