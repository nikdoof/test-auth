import logging

from django_cron import cronScheduler, Job
from eve_api.models.api_player import EVEAccount, EVEPlayerCorporation
import eve_api.api_puller.accounts

class UpdateAPIs(Job):
        """
        Updates all Eve API elements in the database
        """

        # run every 2 hours
        run_every = 7200

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger
                
        def job(self):
            # Update all the eve accounts and related corps
            for acc in EVEAccount.objects.all():
               self._logger.info("Updating UserID %s" % acc.api_user_id)
               if not acc.user:
                   acc.delete()
                   continue
               try:
                   eve_api.api_puller.accounts.import_eve_account(acc.api_key, acc.api_user_id)
                   acc.api_status = 1
               except APIAuthException:
                   acc.api_status = 2

               acc.save()

            for corp in EVEPlayerCorporation.objects.all():
                corp.query_and_update_corp()


cronScheduler.register(UpdateAPIs)
