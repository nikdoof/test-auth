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
                
        def job(self):
            delta = datetime.timedelta(seconds=self.last_update_delay)

            print delta
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


class APIKeyParser:
    dictitems = {}

    def __init__(self, key):
        rows = key.split('\n')
        for row in rows:
            key = row.split(":")[0].replace(" ", "_").lower().strip()
            value = row.split(":")[1].strip()

            self.dictitems[key] = value

    def __getattr__(self, key):
        return self.dictitems[key]

    def __str__(self):
        return "%s:%s" % (self.user_id, self.api_key)

class ProcessValidations():
    """
    Grabs all Reddit Mail and processes validations
    """

    def job(self):
        inbox = Inbox(settings.REDDIT_USER, settings.REDDIT_PASSWD)

        for msg in inbox:
            if not msg.was_comment and msg.new:
                try:
                    acc = RedditAccount.objects.get(username__iexact=msg.author)
                    if not acc.validated and msg.body == acc.user.username:
                        acc.validated = True
                        acc.save()
                except RedditAccount.DoesNotExist:
                    continue
                
