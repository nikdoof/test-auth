import logging
import datetime

from eve_api.models.api_player import EVEAccount, EVEPlayerCorporation
import eve_api.api_puller.accounts
from eve_api.api_exceptions import APIAuthException, APINoUserIDException

class UpdateAPIs():
        """
        Updates all Eve API elements in the database
        """

        settings = { 'update_corp': False }

        last_update_delay = 86400

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger
                
        def job(self):
            # Update all the eve accounts and related corps

            delta = datetime.timedelta(seconds=self.last_update_delay)
            self._logger.debug("Updating APIs older than %s" % (datetime.datetime.now() - delta))

            accounts = EVEAccount.objects.filter(api_last_updated__lt=(datetime.datetime.now() - delta))
            self._logger.debug("%s account(s) to update" % len(accounts))
            for acc in accounts:
               self._logger.info("Updating UserID %s" % acc.api_user_id)
               if not acc.user:
                   acc.delete()
                   continue
               eve_api.api_puller.accounts.import_eve_account(acc.api_key, acc.api_user_id)

            if self.settings['update_corp']:
                for corp in EVEPlayerCorporation.objects.all():
                    try:
                        corp.query_and_update_corp()
                    except:
                        self._logger.error('Error updating %s' % corp)
                        continue
