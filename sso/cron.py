import logging

from django.contrib.auth.models import User, Group
from eve_api.models import EVEAccount
from sso.models import ServiceAccount

class RemoveInvalidUsers():
        """
        Cycles through all users and runs the permission checking routine for
        each profile.
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

class ValidateDisabledUsers():
        """
        Cycles through all users, and disables any Service Account of disabled
        users.
        """

        # run daily
        run_every = 84600

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger

        def job(self):
            for servacc in ServiceAccount.objects.filter(active=0):
                self._logger.info('Checking %s' % servacc)
                if not servacc.service.api_class.disable_user(servacc.service_uid):
                    self._logger.error('Error disabling %s on %s' % (servacc, servacc.service))
