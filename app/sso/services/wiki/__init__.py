import hashlib
import random
from django.db import load_backend, transaction, IntegrityError
from sso.services import BaseDBService
from django.conf import settings

class MediawikiService(BaseDBService):
    """
    Mediawiki Class, allows registration and sign-in

    """

    settings = { 'require_user': False,
                 'require_password': False,
                 'provide_login': False,
                 'use_auth_username': False,
                 'database_name': 'dreddit_wiki' }

    default_options = 'rows=80\ncols=50'


    SQL_ADD_USER = r"INSERT INTO user (user_name, user_password, user_newpassword, user_email, user_options) VALUES (%s, %s, '', %s, %s)"
    SQL_DIS_USER = r"UPDATE user SET user_password = '', user_email = '', user_token = %s WHERE user_name = %s"
    SQL_DIS_GROUP = r"INSERT INTO user_groups (ug_user, ug_group) VALUES ((SELECT user_id FROM user WHERE user_name = %s), 'Disabled')"
    SQL_ENABLE_USER = r"UPDATE user SET user_password = %s WHERE user_name = %s"
    SQL_ENABLE_GROUP = r"DELETE FROM user_groups where ug_user = (SELECT user_id FROM user WHERE user_name = %s) AND ug_group = 'Disabled'"
    SQL_CHECK_USER = r"SELECT user_name from user WHERE user_name = %s"

    SQL_DEL_REV = r"UPDATE revision SET rev_user = (SELECT user_id FROM user WHERE user_name = 'DeletedUser'), rev_user_text = 'DeletedUser' WHERE rev_user = (SELECT user_id FROM user WHERE user_name = %s)"
    SQL_DEL_USER = r"DELETE FROM user WHERE user_name = %s"

    def _gen_salt(self):
        return "%x" % random.randint(0, 2147483647)

    def _gen_mw_hash(self, password, salt=None):
        if not salt:
            salt = self._gen_salt()
        hash = hashlib.md5('%s-%s' % (salt, hashlib.md5(password).hexdigest())).hexdigest()
        return ":B:%s:%s" % (salt, hash)

    def _gen_user_token(self):
        hash = hashlib.md5(self._gen_salt()).hexdigest()
        return hash

    def _clean_username(self, username):
        username = username.strip()
        return username[0].upper() + username[1:]

    def add_user(self, username, password, **kwargs):
        """ Add a user """
        if 'user' in kwargs:
            email = kwargs['user'].email
        else:
            email = ''
        pwhash = self._gen_mw_hash(password)
        self.dbcursor.execute(self.SQL_ADD_USER, [self._clean_username(username), pwhash, email, self.default_options])
        return { 'username': self._clean_username(username), 'password': password }

    def check_user(self, username):
        """ Check if the username exists """
        self.dbcursor.execute(self.SQL_CHECK_USER, [self._clean_username(username)])
        row = self.dbcursor.fetchone()
        if row:
            return True        
        return False

    def delete_user(self, uid):
        """ Delete a user """
        self.dbcursor.execute(self.SQL_DEL_REV, [uid])
        self.dbcursor.execute(self.SQL_DEL_USER, [uid])
        return True

    def disable_user(self, uid):
        """ Disable a user """
        #self.dbcursor.execute(self.SQL_DIS_USER, [self._gen_user_token(), uid])
        try:
            self.dbcursor.execute(self.SQL_DIS_GROUP, [uid])
        except IntegrityError:
            # Record already exists, skip it
            pass
        return True

    def enable_user(self, uid, password):
        """ Enable a user """
        pwhash = self._gen_mw_hash(password)
        self.dbcursor.execute(self.SQL_ENABLE_USER, [pwhash, uid])
        self.dbcursor.execute(self.SQL_ENABLE_GROUP, [uid])
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)
        

ServiceClass = 'MediawikiService'
