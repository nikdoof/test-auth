import time
import datetime
import logging
import settings

from reddit.models import RedditAccount
from reddit.api import Inbox

class UpdateAPIs():
    """
    Updates all Reddit API elements in the database
    """
    @property
    def _logger(self):
        if not hasattr(self, '__logger'):
            self.__logger = logging.getLogger(__name__)
        return self.__logger

    last_update_delay = 604800
            
    def job(self, args):
        delta = datetime.timedelta(seconds=self.last_update_delay)

        self._logger.debug("Updating accounts older than %s" % (datetime.datetime.now() - delta))

        for acc in RedditAccount.objects.filter(last_update__lt=(datetime.datetime.now() - delta)):
            self._logger.info("Updating %s" % acc.username)

            try:
                acc.api_update()
            except RedditAccount.DoesNotExist:
                acc.delete()
            else:
                acc.save()
            time.sleep(.5)
