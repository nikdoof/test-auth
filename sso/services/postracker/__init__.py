import hashlib
import random
from django.db import load_backend, transaction, IntegrityError
from sso.services import BaseDBService
import settings

class POSTrackerService(BaseDBService):
    """
    POS Tracker Class, allows registration.

    """

    settings = { 'require_user': False,
                 'require_password': False,
                 'provide_login': False, 
                 'database_name': 'dreddit_pos' }

    SQL_ADD_USER = r"INSERT INTO pos3_user (eve_id, name, pass, email, access) VALUES (%s, %s, %s, %s, 1)"
    SQL_DIS_USER = r"UPDATE pos3_user SET pass = '', away = 1 WHERE name = %s"
    SQL_DEL_USER = r"DELETE FROM pos3_user WHERE name = %s"
    SQL_ENABLE_USER = r"UPDATE pos3_user SET pass = %s, away = 0 WHERE name = %s"
    SQL_CHECK_USER = r"SELECT name from pos3_user WHERE name = %s"

    def _gen_salt(self):
        return hashlib.md5("%x" % random.randint(0, 2147483647)).hexdigest()[:8]

    def _gen_pwhash(self, password, salt=None):
        if not salt:
            salt = self._gen_salt()
        pwhash = hashlib.md5("%s%s" % (salt, password)).hexdigest()
        return (pwhash, salt)

    def add_user(self, username, password, **kwargs):
        """ Add a user """
        email = kwargs['user'].email
        pwhash, salt = self._gen_pwhash(password)

        if 'eveapi' in kwargs:
            eveid = kwargs['eveapi'].api_user_id
        else:
            eveid = None

        self.dbcursor.execute(self.SQL_ADD_USER, [eveid, username, "%s%s" % (salt, pwhash) , email])
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
        self.dbcursor.execute(self.SQL_DEL_USER, [uid])
        self.db.connection.commit()
        return True

    def disable_user(self, uid):
        """ Disable a user """
        self.dbcursor.execute(self.SQL_DIS_USER, [uid])
        self.db.connection.commit()
        return True

    def enable_user(self, uid, password):
        """ Enable a user """
        pwhash, salt = self._gen_pwhash(password)
        self.dbcursor.execute(self.SQL_ENABLE_USER, ["%s%s" % (salt, pwhash), uid])
        self.db.connection.commit()
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)        

ServiceClass = 'POSTrackerService'
