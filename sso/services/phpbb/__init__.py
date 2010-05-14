import hashlib
import random
from django.db import load_backend, transaction, IntegrityError
from sso.services import BaseDBService
import settings

class PhpBBService(BaseDBService):
    """
    PHPBB Class, allows registration and sign-in

    """

    settings = { 'require_user': False,
                 'require_password': False,
                 'provide_login': False }

    SQL_ADD_USER = r"INSERT INTO phpbb_users (username, username_clean, user_password, user_email) VALUES (%s, %s, %s, %s)"
    SQL_DIS_USER = r"DELETE FROM phpbb_user_groups where user_id = (SELECT user_id FROM phpbb_user WHERE username = %s)"
    SQL_CHECK_USER = r"SELECT username from phpbb_user WHERE username = %s"

    SQL_ADD_USER_GROUP = r"INSERT INTO phpbb_user_group (group_id, user_id) VALUES (%s, %s)"
    SQL_GET_GROUP = r"SELECT group_id from phpbb_groups WHERE group_name = %s"
    SQL_ADD_GROUP = r"INSERT INTO phpbb_groups (group_name) VALUES (%s)"

    def _gen_salt(self):
        return "%x" % random.randint(0, 2147483647)

    def _gen_hash(self, password, salt=None):
        if not salt:
            salt = self._gen_salt()
        hash = hashlib.md5('%s-%s' % (salt, hashlib.md5(password).hexdigest())).hexdigest()
        return ":B:%s:%s" % (salt, hash)

    def add_user(self, username, password, **kwargs):
        """ Add a user """
        if 'user' in kwargs:
            email = kwargs['user'].email
            groups = kwargs['user'].groups.all()
        else:
            email = ''
        pwhash = self._gen_hash(password)

        self._dbcursor.execute(self.SQL_ADD_USER, [username, pwhash, email])
        self._db.connection.commit()

        self.update_groups(username)
        return username

    def update_groups(self, username):
        self._dbcursor.execute(self.SQL_CHECK_USER, [self._clean_username(username)])
        row = self._dbcursor.fetchone()
        user_id = row['user_id']

        for group in groups:
            self._dbcursor.execute(self.SQL_GET_GROUP, [group.name])
            row = self._dbcursor.fetchone()
            if not row:
                self._dbcursor.execute(self.SQL_ADD_GROUP, [group.name])
                self._db.connection.commit()
                self._dbcursor.execute(self.SQL_GET_GROUP, [group.name])
                row = self._dbcursor.fetchone()

            self._dbcursor.execute(self.SQL_ADD_USER_GROUP, [row['group_id'], user_id])
            self._db.connection.commit()

    def check_user(self, username):
        """ Check if the username exists """
        self._dbcursor.execute(self.SQL_CHECK_USER, [self._clean_username(username)])
        row = self._dbcursor.fetchone()
        if row:
            return True        
        return False

    def delete_user(self, uid):
        """ Delete a user """
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
        

ServiceClass = 'PhpBBService'
