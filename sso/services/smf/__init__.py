import hashlib
import random
from sso.services import BaseDBService
import settings

class SMFService(BaseDBService):
    """
    SMF Class, allows registration and sign-in

    """

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False,
                 'use_auth_username': False
                 'can_delete': False }

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
        else:
            email = ''
        pwhash = self._gen_hash(password)

        self._dbcursor.execute(self.SQL_ADD_USER, [username, pwhash, email])

        self.update_groups(username)
        return { 'username': username, 'password': password }

    def update_groups(self, username, groups, character=None):
        self._dbcursor.execute(self.SQL_CHECK_USER, [self._clean_username(username)])
        row = self._dbcursor.fetchone()
        user_id = row['id_member']

        smfgrps = self._get_smf_groups()

        grpids = []
        for group in groups:
            if group.name in smfgrps:
                grpids.append(smfgrps[group.name])
            else:
                grpids.append(self._create_smf_group(group.name))

        # Update DB with grouplist
        self._dbcursor.execute(self.SQL_UPDATE_GROUPS, [user_id, ','.join(groupids)])

    def check_user(self, username):
        """ Check if the username exists """
        self._dbcursor.execute(self.SQL_CHECK_USER, [self._clean_username(username)])
        row = self._dbcursor.fetchone()
        if row:
            return True        
        return False

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)
        

ServiceClass = 'SMFService'
