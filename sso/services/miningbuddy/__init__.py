import crypt
import random
import time
from django.db import load_backend, transaction
from sso.services import BaseDBService
import settings

class MiningBuddyService(BaseDBService):
    """
    Mining Buddy Class, allows registration and sign-in

    """

    settings = { 'require_user': False,
                 'require_password': False,
                 'provide_login': False,
                 'database_name': 'dreddit_mining', 
                 'password_salt': 's98ss7fsc7fd2rf62ctcrlwztstnzve9toezexcsdhfgviuinusxcdtsvbrg' }


    SQL_ADD_USER = r"INSERT INTO users (username, password, email, emailvalid, confirmed, rank) VALUES (%s, %s, %s, 1, 1, 2)"
    SQL_ADD_API = r"INSERT INTO api_keys (userid, time, apiID, apiKey, api_valid, charid) values (%s, %s, %s, %s, 1, %s)"
    SQL_DIS_USER = r"UPDATE users SET canLogin = 0 WHERE username = %s"
    SQL_ENABLE_USER = r"UPDATE users SET canLogin = 1, password = %s WHERE username = %s"
    SQL_CHECK_USER = r"SELECT username from users WHERE username = %s and deleted = 0"
    SQL_DEL_USER = r"UPDATE users set deleted = 1 WHERE username = %s"

    def _gen_salt(self):
        return self.settings['password_salt']

    def _gen_mb_hash(self, password, salt=None):
        if not salt:
            salt = self._gen_salt()
        return crypt.crypt(password, salt)

    def _clean_username(self, username):
        username = username.strip()
        return username

    def add_user(self, username, password, **kwargs):
        """ Add a user """
        pwhash = self._gen_mb_hash(password)
        if 'user' in kwargs:
            email = kwargs['user'].email
        else:
            email = ''

        self.dbcursor.execute(self.SQL_ADD_USER, [self._clean_username(username), pwhash, email])
        self.db.connection.commit()

        userid = self.dbcursor.lastrowid
        if 'eveapi' in kwargs:
            self.dbcursor.execute(self.SQL_ADD_API, [userid, int(time.time()), kwargs['eveapi'].api_user_id, kwargs['eveapi'].api_key, kwargs['character'].id])
            self.db.connection.commit()

        return self._clean_username(username)

    def check_user(self, username):
        """ Check if the username exists """
        self.dbcursor.execute(self.SQL_CHECK_USER, [self._clean_username(username)])
        row = self.dbcursor.fetchone()
        if row:
            return True        
        return False

    def delete_user(self, uid):
        """ Delete a user """
        self.dbcursor.execute(self.SQL_DEL_USER, [uid])
        self.db.connection.commit()

    def disable_user(self, uid):
        """ Disable a user """
        self.dbcursor.execute(self.SQL_DIS_USER, [uid])
        self.db.connection.commit()

    def enable_user(self, uid, password):
        """ Enable a user """
        pwhash = self._gen_mb_hash(password)
        self.dbcursor.execute(self.SQL_ENABLE_USER, [pwhash, uid])
        self.db.connection.commit()
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)
        

ServiceClass = 'MiningBuddyService'
