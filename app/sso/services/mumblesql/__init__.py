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

    def _add_log(self, log):
        self.dbcursor.execute(r"INSERT INTO murmur_slog (server_id, msg) VALUES (%s, %s)", [self.settings['server_id'], log])
        self.commit()

    def _get_id(self, name):
        self.dbcursor.execute(r"SELECT user_id from murmur_users WHERE name = %s AND server_id = %s", [name, self.settings['server_id']])
        row = self.dbcursor.fetchone()
        if row:
            return row[0]

    def _get_groups(self):
        self.dbcursor.execute(r"SELECT group_id, name FROM murmur_groups WHERE server_id = % AND channel_id = 0", [self.settings['server_id']])
        rows = self.dbcursor.fetchall()

        out = {}
        for row in rows:
            out[row[1]] = row[0]

        return out

    def _get_group(self, name):
        self.dbcursor.execute(r"SELECT group_id, name FROM murmur_groups WHERE server_id = % AND channel_id = 0 AND name = %s", [self.settings['server_id'], name])
        row = self.dbcursor.fetchone()
        if row:
            return row[0]

    def _get_user_groups(self, name):
        self.dbcursor.execute(r"SELECT murmur_groups.name FROM murmur_groups, murmur_group_members WHERE murmur_group_members.group_id = murmur_groups.group_id AND murmur_group_members.server_id = murmur_groups.server_id AND murmur_group_members.user_id = %s", [user_id])
        return [row[0] for row in self.dbcursor.fetchall()]

    def _add_group(self, name):
        self.dbcursor.execute(r"SELECT MAX(group_id)+1 FROM murmur_groups")
        row = self.dbcursor.fetchone()
        groupid = row[0]

        self.dbcursor.execute(r"INSERT INTO murmur_groups (group_id, server_id, name, channel_id, inherit, inheritable) VALUES (%s, %s, %s, 0, 1, 1)", [groupid, self.settings['server_id'], name])
        self.commit()

        return groupid

    def _add_user_group(self, userid, groupid):
        self.dbcursor.execute(r"INSERT INTO murmur_group_members (group_id, server_id, user_id, addit) VALUES (%s, %s, %s, 1)", [groupid, self.settings['server_id'], userid])
        self.commit()
        self._add_log("Added user id %s to group id %s" % (userid, groupid))

    def _rem_user_group(self, userid, groupid):
        self.dbcursor.execute(r"DELETE FROM murmur_group_members WHERE group_id = %s AND server_id = %s AND user_id = %s", [groupid, self.settings['server_id'], userid])
        self.commit()

    def add_user(self, username, password, **kwargs):
        """ Add a user """

        username = self._gen_name(kwargs['character'])
        self.dbcursor.execute(r"SELECT max(user_id)+1 as next_id from murmur_users")
        userid = self.dbcursor.fetchone()[0]

        self.dbcursor.execute(r"INSERT INTO murmur_users (server_id, user_id, name, pw) VALUES (%s, %s, %s, %s)", [self.settings['server_id'], userid, username, self._gen_pwhash(password)])
        self.commit()
        return { 'username': username, 'password': password }

    def check_user(self, username):
        """ Check if the username exists """
        self.dbcursor.execute(r"SELECT name from murmur_users WHERE name = %s AND server_id = %s", [username, self.settings['server_id']])
        row = self.dbcursor.fetchone()
        if row and row[0].lower() == username.lower():
            return True        
        return False

    def delete_user(self, uid):
        """ Delete a user """
        id = self._get_id(uid)
        self.dbcursor.execute(r"DELETE FROM murmur_users WHERE user_id = %s AND server_id = %s", [id, self.settings['server_id']])
        self.commit()
        return True

    def disable_user(self, username):
        """ Disable a user """
        uid = self._get_id(username)
        self.dbcursor.execute(r"UPDATE murmur_users SET pw = null WHERE user_id = %s AND server_id = %s", [uid, self.settings['server_id']])
        self.commit()
        self.dbcursor.execute(r"DELETE FROM murmur_user_info WHERE user_id = %s AND server_id = %s AND key = 3", [uid, self.settings['server_id']])
        self.commit()
        return True

    def enable_user(self, uid, password):
        """ Enable a user """
        self.dbcursor.execute(r"UPDATE murmur_users SET pw = %s WHERE name = %s AND server_id = %s", [self._gen_pwhash(password), uid, self.settings['server_id']])
        self.commit()
        return True

    def reset_password(self, uid, password):
        """ Reset the user's password """
        return self.enable_user(uid, password)        

    def update_groups(self, username, groups, character=None):
        """ Update user's groups """

        userid = self._get_id(uid)
        mumble_groups = self._get_groups()
        user_groups = set(self._get_user_groups(userid))
        act_groups = set([g.name.replace(' ', '-').lower() for g in groups])

        addgroups = act_groups - user_groups
        remgroups = user_groups - act_groups

        for g in addgroups:
            if not g in mumble_groups:
                mumble_groups[g] = self._add_group(g)
            self._add_user_group(userid, mumble_groups[g])

        for g in remgroups:
            self._rem_user_group(userid, mumble_group[g])

ServiceClass = 'MumbleSQLService'
