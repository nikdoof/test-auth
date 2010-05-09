import hashlib
import random
from django.db import load_backend, transaction, IntegrityError
from sso.services import BaseService
import settings

class QMSService(BaseService):
    """
    QMS Class, allows registration and sign-in

    """

    settings = { 'require_user': False,
                 'require_password': False,
                 'provide_login': False }

    SQL_ADD_USER = r"INSERT INTO users (ssoid, Name, passhash, salt, Email, certificate) VALUES (%s, %s, %s, %s, %s, %s)"
    SQL_DIS_USER = r"UPDATE users SET passhash = '' WHERE ssoid = %s"
    SQL_ENABLE_USER = r"UPDATE users SET passhash = %s, salt = %s WHERE ssoid = %s"
    SQL_CHECK_USER = r"SELECT ssoid from users WHERE ssoid = %s"

    def __init__(self):

        # Use the master DB settings, bar the database name
        backend = load_backend(settings.DATABASE_ENGINE) 
        self._db = backend.DatabaseWrapper({
            'DATABASE_HOST': settings.DATABASE_HOST,
            'DATABASE_NAME': settings.QMS_DATABASE,
            'DATABASE_OPTIONS': {},
            'DATABASE_PASSWORD': settings.DATABASE_PASSWORD,
            'DATABASE_PORT': settings.DATABASE_PORT,
            'DATABASE_USER': settings.DATABASE_USER,
            'TIME_ZONE': settings.TIME_ZONE,})

        self._dbcursor = self._db.cursor()

    def __del__(self):
        self._db.close()
        self._db = None

    def _gen_salt(self):
        return hashlib.md5("%x" % random.randint(0, 2147483647)).hexdigest()[:6]

    def _gen_pwhash(self, password, salt=None):
        if not salt:
            salt = self._gen_salt()
        pwhash = hashlib.md5(password).hexdigest()
        cert = hashlib.md5('%s%s' % (pwhash, salt)).hexdigest()
        return (pwhash, salt, cert)

    def add_user(self, username, password, **kwargs):
        """ Add a user """
        email = kwargs['user'].email
        pwhash, salt, cert = self._gen_pwhash(password)
        self._dbcursor.execute(self.SQL_ADD_USER, [username, username, pwhash, salt, email, cert])
        self._db.connection.commit()
        return username

    def check_user(self, username):
        """ Check if the username exists """
        self._dbcursor.execute(self.SQL_CHECK_USER, [username])
        row = self._dbcursor.fetchone()
        if row:
            return True        
        return False

    def delete_user(self, uid):
        """ Delete a user """
        #self._dbcursor.execute(self.SQL_DEL_REV, [uid])
        #self._dbcursor.execute(self.SQL_DEL_USER, [uid])
        #self._db.connection.commit()
        return True

    def disable_user(self, uid):
        """ Disable a user """
        self._dbcursor.execute(self.SQL_DIS_USER, [uid])
        self._db.connection.commit()
        return True

    def enable_user(self, uid, password):
        """ Enable a user """
        pwhash, salt = self._gen_pwhash(password)
        self._dbcursor.execute(self.SQL_ENABLE_USER, [pwhash, salt, uid])
        self._db.connection.commit()
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)        

ServiceClass = 'QMSService'
