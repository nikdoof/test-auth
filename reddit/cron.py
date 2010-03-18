import time
import logging

from django_cron import cronScheduler, Job
from reddit.models import RedditAccount
from reddit.api import Inbox

class UpdateAPIs(Job):
        """
        Updates all Reddit API elements in the database
        """

        # run every 24 hours
        run_every = 86400

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger
                
        def job(self):
            for acc in RedditAccount.objects.all():
                acc.api_update()
                acc.save()
                time.sleep(2)


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

class ProcessInbox(Job):
    """
    Grabs all Reddit Mail and processes any new applications
    """

    def job(self):
        inbox = Inbox(settings.REDDIT_USER, settings.REDDIT_PASSWORD)

        for msg in inbox:
            if not msg.was_comment and msg.new:
                try:
                    key = APIKeyParser(msg.body)
                except:
                    pass
                else:
                    print key.username
                

cronScheduler.register(UpdateAPIs)
