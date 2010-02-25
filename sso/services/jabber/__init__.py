from sso.services import BaseService
from sso.services.jabber.ejabberdctl import eJabberdCtl
import settings

class JabberService(BaseService):
    
    def __init__(self):
        self.ejctl = eJabberdCtl(sudo=settings.JABBER_SUDO)

    def add_user(username, password):
        """ Add user to service """
        return self.ejctl.register(username, settings.JABBER_SERVER, password)

    def set_corp(self, username):
        """ User is in corp, enable extra privs """
        return self.ejctl.srg_user_add(username, settings.JABBER_SERVER, settings.JABBER_GROUP)

    def delete_user(self, username):
        """ Delete a user """
        return self.ejctl.unregister(username, settings.JABBER_SERVER)

    def disable_user(self, username):
        """ Disable a user """
        return self.ejctl.ban_user(settings.JABBER_SERVER, username)

    def enable_user(self, username):
        """ Enable a user """
        

    def check_user(self, username):
        """ Check if the username exists """
        if username not in self.ejctl.get_users(settings.JABBER_SERVER):
            return False
        else:
            return True

ServiceClass = 'JabberService'
