from django.conf import settings
from django.db import connections

def get_api(api):

    if settings.DISABLE_SERVICES:
        return BaseService()

    try:
        mod = __import__(api)
    except ImportError:
        raise Exception('Error creating service')

    for i in api.split(".")[1:]:
        mod = getattr(mod, i)

    return getattr(mod, mod.ServiceClass)()

def list_apis():
    import os.path, pkgutil
    pkgpath = os.path.dirname(__file__)
    return [name for _, name, _ in pkgutil.iter_modules([pkgpath])]

class BaseService():
    """
    Base Service class, all service classes should inherit from this

    """

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False }

    def add_user(self, username, password, **kwargs):
        """ Add a user, returns a dict for that user """
        return { 'username': username, 'password': password }

    def check_user(self, username):
        """ Check if the username exists """
        return False

    def check_uid(self, uid):
        """ Check if a UID exists """
        return self.check_user(uid)

    def delete_user(self, uid):
        """ Delete a user by uid """
        return True

    def disable_user(self, uid):
        """ Disable a user by uid """
        return True

    def enable_user(self, uid, password):
        """ Enable a user by uid """       
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return True

    def login(self, uid):
        """ Login the user and provide cookies back """ 
        pass

    def update_groups(self, uid, groups, character=None):
        """" Update the UID's groups based on the provided list """
        pass


class BaseDBService(BaseService):

    @property
    def db(self):
        if not hasattr(self, '_db'):
            self._db = connections[self.settings['database_name']]
        return self._db

    @property
    def dbcursor(self):
        if not hasattr(self, '_dbcursor'):
            self._dbcursor = self.db.cursor()
        return self._dbcursor

