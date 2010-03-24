import logging

from django.contrib.auth.models import User, Group
from eve_api.models import EVEAccount
from sso.models import ServiceAccount

class RemoveInvalidUsers():
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

                # Check each service account and disable access if they're not allowed
                for servacc in ServiceAccount.objects.filter(user=user):
                    if not (set(user.groups.all()) & set(servacc.service.groups.all())):
                        if servacc.active:
                            self._logger.info("User %s is not in allowed group for %s, deleting account" % (user.username, servacc.service))
                            servacc.active = 0
                            servacc.save()
                            servacc.user.message_set.create(message="Your %s account has been disabled due to lack of permissions. If this is incorrect, check your API keys." % (servacc.service))
                        pass
                    else:
                        if not servacc.active:
                            self._logger.info("User %s is now in a allowed group for %s, enabling account" % (user.username, servacc.service))
                            servacc.active = 1
                            servacc.save()
                            servacc.user.message_set.create(message="Your %s account has been re-enabled, you may need to reset your password to access this service again." % (servacc.service))
                            pass

                # For users set to not active, delete all accounts
                if not user.is_active:
                    print "User %s is inactive, disabling related service accounts" % user.username
                    for servacc in ServiceAccount.objects.filter(user=user):
                        servacc.active = 0
                        servacc.save()
                        pass



