import hashlib
import random
from django.db import load_backend, transaction, IntegrityError
from sso.services import BaseDBService
from django.conf import settings

class MumbleSQLService(BaseDBService):
    """
    Mumble Class, allows registration

    """

    settings = { 'require_user': False,
                 'require_password': True,
                 'provide_login': False, 
                 'use_auth_username': False,
                 'database_name': 'test_mumble',
                 'name_format': '%(alliance)s - %(name)s',
                 'server_id': 1 }

    SQL_ADD_USER = r"INSERT INTO murmur_users (server_id, user_id, name, pw) VALUES (%s, %s, %s, %s)"
    SQL_DIS_USER = r"UPDATE murmur_users SET pw = null WHERE name = %s"
    SQL_ENABLE_USER = r"UPDATE murmur_users SET pw = %s WHERE name = %s"
    SQL_CHECK_USER = r"SELECT name from murmur_users WHERE name = %s"

    SQL_GET_NEXT_USER_ID = r"SELECT max(user_id)+1 as next_id from murmur_users"
    SQL_GET_USER_ID = r"SELECT user_id from murmur_users WHERE name = %s"

    @staticmethod
    def _gen_pwhash(password):
        return hashlib.sha1(password).hexdigest()

    def _gen_name(self, character):
        details = { 'name': character.name,
                    'corporation': character.corporation.ticker }
        if character.corporation.alliance:
            details['alliance'] = character.corporation.alliance.ticker
        else:
            details['alliance'] = None
        return self.settings['name_format'] % details

    def add_user(self, username, password, **kwargs):
        """ Add a user """

        username = self._gen_name(kwargs['character'])
        self.dbcursor.execute(self.SQL_GET_NEXT_USER_ID)
        userid = self.dbcursor.fetchone()[0]

        self.dbcursor.execute(self.SQL_ADD_USER, [self.settings['server_id'], userid, username, self._gen_pwhash(password)])
        transaction.commit_unless_managed()
        return { 'username': username, 'password': password }

    def check_user(self, username):
        """ Check if the username exists """
        self.dbcursor.execute(self.SQL_CHECK_USER, [username])
        row = self.dbcursor.fetchone()
        if row and row[0].lower() == username.lower():
            return True        
        return False

    def delete_user(self, uid):
        """ Delete a user """
        #self.dbcursor.execute(self.SQL_DEL_REV, [uid])
        #self.dbcursor.execute(self.SQL_DEL_USER, [uid])
        return True

    def disable_user(self, uid):
        """ Disable a user """
        self.dbcursor.execute(self.SQL_DIS_USER, [uid])
        transaction.commit_unless_managed()
        return True

    def enable_user(self, uid, password):
        """ Enable a user """
        self.dbcursor.execute(self.SQL_ENABLE_USER, [self._gen_pwhash(password), uid])
        transaction.commit_unless_managed()
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)        

    def update_groups(self, uid, groups, character=None):
        """ Update user's groups """
        pass

ServiceClass = 'MumbleSQLService'
