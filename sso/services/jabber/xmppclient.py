import time
import xmpp 

class JabberAdmin():
    """ Adds a jabber user to a remote Jabber server """

    def __init__(self, server, username, password, ip=None):

        self.server = server
        self.username = username
        self.password = password

        self.jid = xmpp.protocol.JID('%s@%s' % (username, server))

        if not ip:
            self._connect_addr = server
        else:
            self._connect_addr = ip


    def __del__(self):
        self._client.disconnect()

    def connect(self):
        if not hasattr(self, '_client'):
            client = xmpp.Client(self.jid.getDomain(), debug=[])

            client.connect(server=('dredd.it', 5222))
            client.auth(self.username, self.password)
            client.sendInitPresence()

            self._client = client

    def _construct_iq_req(self, xmlns, node):
        n = xmpp.Node('command', attrs={'xmlns': xmlns, 'node': node})
        iq = xmpp.Protocol('iq', self.server, 'set', payload=[n])
        return iq

    def _construct_form(self, xmlns, node, session, values):

        n = xmpp.Node('command', attrs={'xmlns': xmlns, 'node': node, 'sessionid': session})
        x = n.addChild('x', namespace='jabber:x:data', attrs={ 'type': 'submit' })

        for v in values:
            type, var, value = v
            x.addChild('field', attrs={'type': type, 'var': var}).addChild('value').addData(value)

        return xmpp.Protocol('iq', self.server, 'set', payload=[n])


    def adduser(self, username, password):
        try:
            self.connect()
        except:
            return False
        # Send request and get the Session ID
        resp = self._client.SendAndWaitForResponse(self._construct_iq_req('http://jabber.org/protocol/commands', 'http://jabber.org/protocol/admin#add-user'))
        sessionid = resp.getTagAttr('command','sessionid')

        values = [ ('hidden', 'FORM_TYPE', 'http://jabber.org/protocol/admin'),
                   ('jid-single', 'accountjid', username),
                   ('text-private', 'password', password),
                   ('text-private', 'password-verify', password) ]

        iq = self._construct_form('http://jabber.org/protocol/commands', 'http://jabber.org/protocol/admin#add-user', sessionid, values)

        # Send request and pray for the best
        resp = self._client.SendAndWaitForResponse(iq)

        if resp.getAttrs()['type'] == "result":
            return True
        else:
            return False


    def deluser(self, username):
        try:
            self.connect()
        except:
            return False
        # Send request and get the Session ID
        resp = self._client.SendAndWaitForResponse(self._construct_iq_req('http://jabber.org/protocol/commands', 'http://jabber.org/protocol/admin#delete-user'))
        sessionid = resp.getTagAttr('command','sessionid')

        values = [ ('hidden', 'FORM_TYPE', 'http://jabber.org/protocol/admin'),
                   ('jid-multi', 'accountjids', username) ]

        iq = self._construct_form('http://jabber.org/protocol/commands', 'http://jabber.org/protocol/admin#delete-user', sessionid, values)

        # Send request and pray for the best
        resp = self._client.SendAndWaitForResponse(iq)

        if resp.getAttrs()['type'] == "result":
            return True
        else:
            return False

    def resetpassword(self, username, password):
        try:
            self.connect()
        except:
            return False
        # Send request and get the Session ID
        resp = self._client.SendAndWaitForResponse(self._construct_iq_req('http://jabber.org/protocol/commands', 'http://jabber.org/protocol/admin#change-user-password'))
        sessionid = resp.getTagAttr('command','sessionid')

        values = [ ('hidden', 'FORM_TYPE', 'http://jabber.org/protocol/admin'),
                   ('jid-single', 'accountjid', username),
                   ('text-private', 'password', password) ]

        iq = self._construct_form('http://jabber.org/protocol/commands', 'http://jabber.org/protocol/admin#change-user-password', sessionid, values)

        # Send request and pray for the best
        resp = self._client.SendAndWaitForResponse(iq)

        if resp.getAttrs()['type'] == "result":
            return True
        else:
            return False


    def checkuser(self, username):
        try:
            self.connect()
        except:
            return False
        # Send request and get the Session ID
        resp = self._client.SendAndWaitForResponse(self._construct_iq_req('http://jabber.org/protocol/commands', 'http://jabber.org/protocol/admin#get-user-password'))
        sessionid = resp.getTagAttr('command','sessionid')

        values = [ ('hidden', 'FORM_TYPE', 'http://jabber.org/protocol/admin'),
                   ('jid-single', 'accountjid', username) ]

        iq = self._construct_form('http://jabber.org/protocol/commands', 'http://jabber.org/protocol/admin#get-user-password', sessionid, values)

        # Send request and pray for the best
        resp = self._client.SendAndWaitForResponse(iq)

        try:
            val = resp.getTag('command').getTag('x').getTag('field', attrs={'label': 'Password'}).getTag('value').getData()
        except AttributeError:
            return False

        if not val.strip() == '':
            return True

        return False
