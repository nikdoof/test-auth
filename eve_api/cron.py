import logging

from eve_api.models.api_player import EVEAccount, EVEPlayerCorporation
import eve_api.api_puller.accounts
from eve_api.api_exceptions import APIAuthException, APINoUserIDException

class UpdateAPIs():
        """
        Updates all Eve API elements in the database
        """

        settings = { 'update_corp': False }

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

            if self.settings['update_corp']:
                for corp in EVEPlayerCorporation.objects.all():
                    try:
                        corp.query_and_update_corp()
                    except:
                        self._logger.error('Error updating %s' % corp)
                        continue
