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
    SQL_DEL_USER = r"DELETE FROM user WHERE username = %s"

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

    def add_user(self, username, password):
        """ Add a user """
        pwhash = self._gen_mw_hash(password)
        self._dbcursor.execute(self.SQL_ADD_USER, [username.strip().capitalize(), pwhash])
        self._db.connection.commit()

    def delete_user(self, username):
        """ Delete a user """
        self._dbcursor.execute(self.SQL_DEL_USER, [username])
        self._db.connection.commit()

    def disable_user(self, username):
        """ Disable a user """
        pass

    def enable_user(self, username, password):
        """ Enable a user """
        pass

    def check_user(self, username):
        """ Check if the username exists """
        pass

ServiceClass = 'MediawikiService'
