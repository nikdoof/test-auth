import crypt
import random
import time
from django.db import load_backend, transaction
from sso.services import BaseService
import settings

class MiningBuddyService(BaseService):
    """
    Mining Buddy Class, allows registration and sign-in

    """

    settings = { 'require_user': False,
                 'require_password': False,
                 'provide_login': False }


    SQL_ADD_USER = r"INSERT INTO users (username, password, email, emailvalid, confirmed, rank) VALUES (%s, %s, %s, 1, 1, 2)"
    SQL_ADD_API = r"INSERT INTO api_keys (userid, time, apiID, apiKey, api_valid, charid) values (%s, %s, %s, %s, 1, %s)"
    SQL_DIS_USER = r"UPDATE users SET canLogin = 0 WHERE username = %s"
    SQL_ENABLE_USER = r"UPDATE users SET canLogin = 1, password = %s WHERE username = %s"
    SQL_CHECK_USER = r"SELECT username from users WHERE username = %s and deleted = 0"
    SQL_DEL_USER = r"UPDATE users set deleted = 1 WHERE username = %s"

    def __init__(self):

        # Use the master DB settings, bar the database name
        backend = load_backend(settings.DATABASE_ENGINE) 
        self._db = backend.DatabaseWrapper({
            'DATABASE_HOST': settings.DATABASE_HOST,
            'DATABASE_NAME': settings.MINING_DATABASE,
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
        return settings.MINING_SALT

    def _gen_mb_hash(self, password, salt=None):
        if not salt:
            salt = self._gen_salt()
        return crypt.crypt(password, salt)

    def _clean_username(self, username):
        username = username.strip()
        return username[0].upper() + username[1:]

    def add_user(self, username, password, **kwargs):
        """ Add a user """
        pwhash = self._gen_mb_hash(password)
        if 'user' in kwargs:
            email = kwargs['user'].email
        else:
            email = ''

        self._dbcursor.execute(self.SQL_ADD_USER, [self._clean_username(username), pwhash, email])
        self._db.connection.commit()

        userid = self._dbcursor.lastrowid
        if 'eveapi' in kwargs:
            self._dbcursor.execute(self.SQL_ADD_API, [userid, int(time.time()), kwargs['eveapi'].api_user_id, kwargs['eveapi'].api_key, kwargs['character'].id])
            self._db.connection.commit()

        return self._clean_username(username)

    def check_user(self, username):
        """ Check if the username exists """
        self._dbcursor.execute(self.SQL_CHECK_USER, [self._clean_username(username)])
        row = self._dbcursor.fetchone()
        if row:
            return True        
        return False

    def delete_user(self, uid):
        """ Delete a user """
        self._dbcursor.execute(self.SQL_DEL_USER, [uid])
        self._db.connection.commit()

    def disable_user(self, uid):
        """ Disable a user """
        self._dbcursor.execute(self.SQL_DIS_USER, [uid])
        self._db.connection.commit()

    def enable_user(self, uid, password):
        """ Enable a user """
        pwhash = self._gen_mb_hash(password)
        self._dbcursor.execute(self.SQL_ENABLE_USER, [pwhash, uid])
        self._db.connection.commit()
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)
        

ServiceClass = 'MiningBuddyService'
