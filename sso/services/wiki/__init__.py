import hashlib
import random
from django.db import load_backend, transaction, IntegrityError
from sso.services import BaseService
import settings

class MediawikiService(BaseService):
    """
    Mediawiki Class, allows registration and sign-in

    """

    settings = { 'require_user': False,
                 'require_password': False,
                 'provide_login': False }

    SQL_ADD_USER = r"INSERT INTO user (user_name, user_password, user_newpassword, user_email) VALUES (%s, %s, '', %s)"
    SQL_DIS_USER = r"UPDATE user SET user_password = '', user_email = '', user_token = %s WHERE user_name = %s"
    SQL_DIS_GROUP = r"INSERT INTO user_groups (ug_user, ug_group) VALUES ((SELECT user_id FROM user WHERE user_name = %s), 'Disabled')"
    SQL_ENABLE_USER = r"UPDATE user SET user_password = %s WHERE user_name = %s"
    SQL_ENABLE_GROUP = r"DELETE FROM user_groups where ug_user = (SELECT user_id FROM user WHERE user_name = %s) AND ug_group = 'Disabled'"
    SQL_CHECK_USER = r"SELECT user_name from user WHERE user_name = %s"

    SQL_DEL_REV = r"UPDATE revision SET rev_user = (SELECT user_id FROM user WHERE user_name = 'DeletedUser'), rev_user_text = 'DeletedUser' WHERE rev_user = (SELECT user_id FROM user WHERE user_name = %s)"
    SQL_DEL_USER = r"DELETE FROM user WHERE user_name = %s"

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

    def __del__(self):
        self._db.close()
        self._db = None

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
        self._dbcursor.execute(self.SQL_ADD_USER, [self._clean_username(username), pwhash, email])
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
        self._dbcursor.execute(self.SQL_DEL_REV, [uid])
        self._dbcursor.execute(self.SQL_DEL_USER, [uid])
        self._db.connection.commit()
        return True

    def disable_user(self, uid):
        """ Disable a user """
        #self._dbcursor.execute(self.SQL_DIS_USER, [self._gen_user_token(), uid])
        try:
            self._dbcursor.execute(self.SQL_DIS_GROUP, [uid])
        except IntegrityError:
            # Record already exists, skip it
            pass
        self._db.connection.commit()
        return True

    def enable_user(self, uid, password):
        """ Enable a user """
        pwhash = self._gen_mw_hash(password)
        self._dbcursor.execute(self.SQL_ENABLE_USER, [pwhash, uid])
        self._db.connection.commit()
        self._dbcursor.execute(self.SQL_ENABLE_GROUP, [uid])
        self._db.connection.commit()
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)
        

ServiceClass = 'MediawikiService'
