import hashlib
import random
from django.db import load_backend, transaction
from sso.services import BaseService
import settings

class MediawikiService(BaseService):
    """
    Mediawiki Class, allows registration and sign-in

    """

    settings = { 'require_user': False,
                 'require_password': False,
                 'provide_login': True }


    SQL_ADD_USER = r"INSERT INTO user (user_name, user_password, user_newpassword, user_options, user_email) VALUES (%s, %s, '', '', '')"
    SQL_DIS_USER = r"UPDATE user SET user_password = '', user_email = '' WHERE user_name = %s"
    SQL_ENABLE_USER = r"UPDATE user SET user_password = %s WHERE user_name = %s"
    SQL_CHECK_USER = r"SELECT user_name from user WHERE user_name = %s"

    def __init__(self):

        # Use the master DB settings, bar the database name
        backend = load_backend(settings.DATABASE_ENGINE) 
        self._db = backend.DatabaseWrapper({
            'DATABASE_HOST': settings.DATABASE_HOST,
            'DATABASE_NAME': settings.WIKI_DATABASE,
            'DATABASE_OPTIONS': {},
            'DATABASE_PASSWORD': settings.DATABASE_PASSWORD,
            'DATABASE_PORT': settings.DATABASE_PORT,
            'DATABASE_USER': settings.DATABASE_USER,
            'TIME_ZONE': settings.TIME_ZONE,})

        self._dbcursor = self._db.cursor()

    def _gen_salt(self):
        return "%x" % random.randint(0, 2147483647)

    def _gen_mw_hash(self, password, salt=None):
        if not salt:
            salt = self._gen_salt()
        hash = hashlib.md5('%s-%s' % (salt, hashlib.md5(password).hexdigest())).hexdigest()
        return ":B:%s:%s" % (salt, hash)

    def _clean_username(self, username):
        username = username.strip()
        return username[0].upper() + username[1:]

    def add_user(self, username, password):
        """ Add a user """
        pwhash = self._gen_mw_hash(password)
        self._dbcursor.execute(self.SQL_ADD_USER, [self._clean_username(username), pwhash])
        self._db.connection.commit()
        return self._clean_username(username)

    def delete_user(self, username):
        """ Delete a user """
        self.disable_user(username)

    def disable_user(self, username):
        """ Disable a user """
        self._dbcursor.execute(self.SQL_DIS_USER, [self._clean_username(username)])
        self._db.connection.commit()

    def enable_user(self, username, password):
        """ Enable a user """
        pwhash = self._gen_mw_hash(password)
        self._dbcursor.execute(self.SQL_ENABLE_USER, [pwhash, self._clean_username(username)])
        pass

    def check_user(self, username):
        """ Check if the username exists """
        self._dbcursor.execute(self.SQL_CHECK_USER, [self._clean_username(username)])
        row = self._dbcursor.fetchone()

        if row:
            return True
        
        return False

ServiceClass = 'MediawikiService'
