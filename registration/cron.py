import logging

from registration.models import RegistrationProfile

class RemoveExpiredProfiles():
        """
        Deletes expired profile requests
        """

        # run every 2 hours
        run_every = 7200

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger
                
        def job(self):
            RegistrationProfile.objects.delete_expired_users()
