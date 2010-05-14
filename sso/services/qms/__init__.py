import hashlib
import random
from django.db import load_backend, transaction, IntegrityError
from sso.services import BaseDBService
import settings

class QMSService(BaseDBService):
    """
    QMS Class, allows registration and sign-in

    """

    settings = { 'require_user': False,
                 'require_password': False,
                 'provide_login': False, 
                 'database_name': 'dreddit_qms' }

    SQL_ADD_USER = r"INSERT INTO users (ssoid, Name, passhash, salt, Email, certificate) VALUES (%s, %s, %s, %s, %s, %s)"
    SQL_DIS_USER = r"UPDATE users SET passhash = '' WHERE ssoid = %s"
    SQL_ENABLE_USER = r"UPDATE users SET passhash = %s, salt = %s, certificate = %s WHERE ssoid = %s"
    SQL_CHECK_USER = r"SELECT ssoid from users WHERE ssoid = %s"

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
        self.dbcursor.execute(self.SQL_ADD_USER, [username, username, pwhash, salt, email, cert])
        self.db.connection.commit()
        return username

    def check_user(self, username):
        """ Check if the username exists """
        self.dbcursor.execute(self.SQL_CHECK_USER, [username])
        row = self.dbcursor.fetchone()
        if row:
            return True        
        return False

    def delete_user(self, uid):
        """ Delete a user """
        #self.dbcursor.execute(self.SQL_DEL_REV, [uid])
        #self.dbcursor.execute(self.SQL_DEL_USER, [uid])
        #self.db.connection.commit()
        return True

    def disable_user(self, uid):
        """ Disable a user """
        self.dbcursor.execute(self.SQL_DIS_USER, [uid])
        self.db.connection.commit()
        return True

    def enable_user(self, uid, password):
        """ Enable a user """
        pwhash, salt, cert = self._gen_pwhash(password)
        self.dbcursor.execute(self.SQL_ENABLE_USER, [pwhash, salt, cert, uid])
        self.db.connection.commit()
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)        

ServiceClass = 'QMSService'
