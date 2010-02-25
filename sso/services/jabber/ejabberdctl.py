import subprocess
import shlex
import StringIO

class CommandError():
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class eJabberdCtl():
    """ Python abstraction of ejabberdctl """
    
    def __init__(self, sudo=False, ejctl='/usr/sbin/ejabberdctl'):
        if sudo:
            self.ejctl = ['sudo',ejctl]
        else:
            self.ejctl = [ejctl]

    def _execute(self, commandline):
        """ Execute a ejabberd command """
        
        args = []
        args.extend(self.ejctl)
        args.extend(shlex.split(commandline.encode('ascii')))

        # Convert all arguments to ascii first
        #args = map(lambda x: x.encode('ascii'), args) 

        print 'Executing: %s' % " ".join(args)

        try:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE)
            proc.wait()
            out = proc.communicate()
            ret = proc.returncode
            #print "%d: %s" % (ret, out)
        except OSError, e:
            raise CommandError('Error encountered during execution: %s' % e)
        if ret > 0:
            raise CommandError('Error: return code is %s' % ret)
        elif ret < 0:
            raise CommandError('Terminated by signal %s' % ret)

        return out[0]

    def status():
         """ Returns the server status """
         pass

    def stop():
         """ Stop the ejabberd server """
         pass

    def restart():
         """ Restart the ejabberd server """
         pass

    def reopen_log():
         """ Reopen the ejabberd log file """
         pass

    def register(self, user, server, password):
         """ Adds a user to a vhost """

         cmd = 'register %s %s %s' % (user, server, password)

         try:
             self._execute(cmd)
         except CommandError, e:
             return False
         else:
             return True

    def unregister(self, user, server):
         """ Deletes a user from a vhost """

         cmd = "unregister %s %s" % (user, server)

         try:
             self._execute(cmd)
         except CommandError, e:
             return False
         else:
             return True

    def backup(self, file):
        """ Backup the ejabberd database to a file """
        pass

    def restore(self, file):
        """ Restore a backup file to the database """
        pass

    def install_fallback(self, file):
        """ Install a database fallback file """
        pass

    def dump(self, file):
        """ Dump the database to a text file """
        pass

    def load(self, file):
        """ Load a database from a text file """
        pass

    def delete_expired_messages(self):
        """ Delete expired offline messages from the database """
 
        cmd = "delete-expired-messages"

        try:
            self._execute(cmd)
        except CommandError, e:
            return False
        else:
            return True

    def delete_old_messages(self, n):
        """ Delete offline messages older than n days from the database """
        cmd = "delete-old-messages %s" % n

        try:
            self._execute(cmd)
        except CommandError, e:
            return False
        else:
            return True

    def status_list(self, status):
         """ Gets a list of users with the specified status """

         cmd = "status-list %s" % status

         try:
             cmdout = self._execute(cmd)
         except CommandError, e:
             return 0
         else:
             out = {}
             lines = cmdout[:-1].split('\n')
             for item in lines:
                 u = item.split(' ')
                 if not hasattr(out, u[0]):
                     out[u[0]] = {}
                 out[u[0]][u[1]] = u[2:]

             return out

    def set_password(self, user, server, password):    

        cmd = "set-password %s %s %s" % (user, server, password)

        try:
            self._execute(cmd)
        except CommandError, e:
            return False
        else:
            return True

    def is_online(self, user, server):
         """ Returns a boolean of if the user is currently online """

         cmd = "user-resources %s %s" % (user, server)

         try:
             out = self._execute(cmd)
         except CommandError, e:
             return False
         else:
             if len(out) > 0:
                 return True
             else:
                 return False

    def online_users(self, server=None):
         """ Gives the number of online users server-wide or for a particular vhost """

         if server:
             cmd = "vhost %s stats onlineusers" % server
         else:
             cmd = "connected-users-number"

         try:
             out = self._execute(cmd)
         except CommandError, e:
             return 0
         else:
             return int(out)

    def get_users(self, server):
         """ Gets a list of users for a specific vhost """

         cmd = "vhost %s registered-users" % server
         try:
             out = self._execute(cmd)
         except CommandError, e:
             return []
         else:
             return out[:-1].split('\n')


    def get_shared_groups(self, server):
         """ Gets a list of Shared Roster Groups (SRGs) for a specific vhost """

         cmd = "srg-list-groups %s" % server

         try:
             out = self._execute(cmd)
         except CommandError, e:
             return 0
         else:
             return out[:-1].split('\n')

    def ban_user(self, server, user, reason="Banned"):
         """ Bans a user, and kicks them off the server  """

         cmd = "vhost %s ban-account %s %s" % (server, user, reason)

         try:
             self._execute(cmd)
         except CommandError, e:
             return False
         else:
             return True

if __name__ == '__main__':
    b = eJabberdCtl(sudo=True)

    print b.register('test88','dredd.it','bleh')
    print b.is_online('matalok', 'dredd.it')

    print b.online_users()
    print b.online_users('dredd.it')
    print b.get_shared_groups('dredd.it')
    print b.get_users('dredd.it')
    print b.status_list('available')
    print b.set_password('matalok', 'dredd.it', 'br6feoot')
