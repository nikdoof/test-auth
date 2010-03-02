import time
import logging

from django_cron import cronScheduler, Job
from reddit.models import RedditAccount

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

cronScheduler.register(UpdateAPIs)
