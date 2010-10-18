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

        settings = { 'update_corp': False }

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

            if self.settings['update_corp']:
                for corp in EVEPlayerCorporation.objects.all():
                    try:
                        corp.query_and_update_corp()
                    except:
                        self._logger.error('Error updating %s' % corp)
                        continue

class CorpManagementUpdate():
        """
        Pulls character information from corp directors marked in the DB
        """

        settings = { 'update_corp': False }

        last_update_delay = 86400
        batches = 50

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger

        def job(self, args):
            directors = EVEPlayerCharacter.objects.filter(director=True)

            for director in directors:
                if len(director.eveaccount_set.all()):
                    api = director.eveaccount_set.all()[0]
                    if api.api_keytype == API_KEYTYPE_FULL:
                        self._logger.info("Updating: %s / %s" % (director, director.corporation))
                        pull_corp_members(api.api_key, api.api_user_id, director.id)
                        director.corporation.query_and_update_corp()

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

