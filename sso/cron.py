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


