import logging
import datetime

from eve_api.models.api_player import EVEAccount, EVEPlayerCorporation, EVEPlayerCharacter
import eve_api.api_puller.accounts
from eve_api.api_puller.alliances import __start_full_import as alliance_import
from eve_api.api_puller.corp_management import pull_corp_members
from eve_api.api_exceptions import APIAuthException, APINoUserIDException
from eve_api.app_defines import *

class UpdateAPIs():
        """
        Updates all Eve API elements in the database
        """

        settings = { 'update_corp': True }

        last_update_delay = 86400
        batches = 50

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger
                
        def job(self, args):
            # Update all the eve accounts and related corps

            delta = datetime.timedelta(seconds=self.last_update_delay)
            self._logger.debug("Updating APIs older than %s" % (datetime.datetime.now() - delta))

            accounts = EVEAccount.objects.filter(api_last_updated__lt=(datetime.datetime.now() - delta)).exclude(api_status=API_STATUS_ACC_EXPIRED).exclude(api_status=API_STATUS_AUTH_ERROR).order_by('api_last_updated')[:self.batches]
            self._logger.debug("%s account(s) to update" % len(accounts))
            for acc in accounts:
               self._logger.info("Updating UserID %s" % acc.api_user_id)
               if not acc.user:
                   acc.delete()
                   continue
               eve_api.api_puller.accounts.import_eve_account(acc.api_key, acc.api_user_id)
               if acc.api_status == API_STATUS_OK:
                   if acc.api_keytype == API_KEYTYPE_FULL and acc.characters.filter(director=1).count():
                       for char in acc.characters.filter(director=1):
                           pull_corp_members(acc.api_key, acc.api_user_id, char.id)
                           director.corporation.query_and_update_corp()

                   if self.settings['update_corp']:
                       for char in acc.characters.all():
                        try:
                            char.corporation.query_and_update_corp()
                        except:
                            self._logger.error('Error updating %s' % corp)
                        continue

class AllianceUpdate():
        """
        Pulls the AllianceList.xml.aspx and updates the alliance objects
        """

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger

        def job(self, args):
            alliance_import()
