from sso.services import BaseService
import settings

if settings.JABBER_METHOD="xmpp":
    from sso.services.xmppclient import JabberAdmin
else:
    from sso.services.jabber.ejabberdctl import eJabberdCtl

class JabberService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False }

    def __init__(self):
        if settings.JABBER_METHOD="xmpp":
            self.method = "xmpp"
            self.jabberadmin = JabberAdmin(settings.JABBER_SERVER, settings.JABBER_AUTH_USER, settings.JABBER_AUTH_PASSWD)
            self.jabberadmin.connect()
        else:
            self.method = "cmd"
            self.ejctl = eJabberdCtl(sudo=settings.JABBER_SUDO)

    def add_user(self, username, password):
        """ Add user to service """
        if self.method = "xmpp":
            return self.jabberadmin.adduser('%s@%s' % (username, settings.JABBER_SERVER), username, password)
        else:
            return self.ejctl.register(username.lower(), settings.JABBER_SERVER, password)

    def delete_user(self, username):
        """ Delete a user """
        if self.method = "xmpp":
            return self.jabberadmin.deluser('%s@%s' % (username, settings.JABBER_SERVER), username, password)
        else:
            return self.ejctl.unregister(username.lower(), settings.JABBER_SERVER)

    def disable_user(self, username):
        """ Disable a user """
        if self.method = "xmpp":
            return False
        else:
            return self.ejctl.ban_user(settings.JABBER_SERVER, username.lower())

    def enable_user(self, username):
        """ Enable a user """
        if self.method = "xmpp":
            return False
        else:
            return self.ejctl.enable_user(settings.JABBER_SERVER, username.lower(), password)

    def check_user(self, username):
        """ Check if the username exists """
        if self.method = "xmpp":
            return self.jabberadmin.checkuser("%s@%s" % (username, settings.JABBER_SERVER))
        eif username.lower() not in self.ejctl.get_users(settings.JABBER_SERVER):
            return False
        else:
            return True

ServiceClass = 'JabberService'
