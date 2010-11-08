import logging
import datetime

from eve_api.models.api_player import EVEAccount, EVEPlayerCorporation, EVEPlayerCharacter
import eve_api.api_puller.accounts
from eve_api.api_puller.alliances import __start_full_import as alliance_import
from eve_api.api_puller.corp_management import pull_corp_members
from eve_api.api_exceptions import APIAuthException, APINoUserIDException
from eve_api.app_defines import *

from eve_api.tasks import *

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
