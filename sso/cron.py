import logging

from django_cron import cronScheduler, Job
from django.contrib.auth.models import User, Group
from eve_api.models import EVEAccount
from sso.models import ServiceAccount

class RemoveInvalidUsers(Job):
        """
        Cycles through all users, check if their permissions are correct.
        """

        # run every 2 hours
        run_every = 7200

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger
                
        def job(self):
            for user in User.objects.all():
                # For each user, update access list based on Corp details
                user.get_profile().update_access()

                # Check each service account and delete access if they're not allowed
                for servacc in ServiceAccount.objects.filter(user=user):
                    if not servacc.service.group in user.groups:
                        self._logger.info("User %s is not in allowed group for %s, deleting account" % (user.username, servacc.service))
                        #servacc.delete()
                        pass

                # For users set to not active, delete all accounts
                if not user.is_active:
                    self._logger.info("User %s is inactive, deleting related service accounts" % user.username)
                    for servacc in ServiceAccount.objects.filter(user=user):
                        #servacc.delete()
                        pass


cronScheduler.register(RemoveInvalidUsers)

if __name__ == '__main__':
    c = RemoveInvalidUsers()
    c.job()
