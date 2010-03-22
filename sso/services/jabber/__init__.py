from sso.services import BaseService
import settings

if settings.JABBER_METHOD == "xmpp":
    from sso.services.jabber.xmppclient import JabberAdmin
else:
    from sso.services.jabber.ejabberdctl import eJabberdCtl

class JabberService(BaseService):

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False }

    def __init__(self):
        if settings.JABBER_METHOD == "xmpp":
            self.method = "xmpp"
            self.jabberadmin = JabberAdmin(settings.JABBER_SERVER, settings.JABBER_AUTH_USER, settings.JABBER_AUTH_PASSWD)
            self.jabberadmin.connect()
        else:
            self.method = "cmd"
            self.ejctl = eJabberdCtl(sudo=settings.JABBER_SUDO)

    def add_user(self, username, password, **kwargs):
        """ Add user to service """
        if self.method == "xmpp":
            if self.jabberadmin.adduser('%s@%s' % (username, settings.JABBER_SERVER), password):
                return '%s@%s' % (username, settings.JABBER_SERVER)
        else:
            if self.ejctl.register(username.lower(), settings.JABBER_SERVER, password):
                return '%s@%s' % (username, settings.JABBER_SERVER)

    def check_user(self, username):
        """ Check if the username exists """
        if self.method == "xmpp":
            return self.jabberadmin.checkuser("%s@%s" % (username, settings.JABBER_SERVER))
        elif username.lower() not in self.ejctl.get_users(settings.JABBER_SERVER):
            return False
        else:
            return True

    def delete_user(self, uid):
        """ Delete a user """
        if self.method == "xmpp":
            return self.jabberadmin.deluser(uid)
        else:
            username, server = uid.split("@")
            return self.ejctl.unregister(username, server)

    def disable_user(self, uid):
        """ Disable a user """
        if self.method == "xmpp":
            return False
        else:
            username, server = uid.split("@")
            return self.ejctl.ban_user(server, username)

    def enable_user(self, uid, password):
        """ Enable a user """
        if self.method == "xmpp":
            return False
        else:
            username, server = uid.split("@")
            return self.ejctl.enable_user(server, username, password)

    def reset_password(self, uid, password):
        """ Reset the user's password """
        if self.method == "xmpp":
            return self.jabberadmin.resetpassword(uid, password)
        else:
            username, server = uid.split("@")
            return self.ejctl.set_password(server, username, password)

ServiceClass = 'JabberService'
