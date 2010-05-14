import settings

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
        """ Add a user, returns a UID for that user """
        return username

    def check_user(self, username):
        """ Check if the username exists """
        return False

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

    def login(uid):
        """ Login the user and provide cookies back """ 
        pass


class BaseDBService(BaseService):

    @property
    def _db(self):
        if not hasattr(self, '_db'):
            # Use the master DB settings, bar the database name
            backend = load_backend(settings.DATABASE_ENGINE)
            self._db = backend.DatabaseWrapper({
                'DATABASE_HOST': settings.DATABASE_HOST,
                'DATABASE_NAME': self.settings['database_name'],
                'DATABASE_OPTIONS': {},
                'DATABASE_PASSWORD': settings.DATABASE_PASSWORD,
                'DATABASE_PORT': settings.DATABASE_PORT,
                'DATABASE_USER': settings.DATABASE_USER,
                'TIME_ZONE': settings.TIME_ZONE,})

        return self._db

    @property
    def _dbcursor(self):
        return self._db.dbcursor()

    def __del__(self):
        if hasattr(self, '_db'):
            self._db.connection.commit()
            self._db.close()
            self._db = None

