from urllib2 import HTTPError, URLError
from celery.task import Task
from celery.decorators import task
from reddit.models import RedditAccount
from reddit.api import Inbox, LoginError
from django.conf import settings

class send_reddit_message(Task):

    default_retry_delay = 5 * 60 # retry in 5 minutes
    ignore_result = True

    def run(self, to, subject, message, **kwargs):
        logger = self.get_logger(**kwargs)

        logger.info("Sending Reddit message to %s" % to)
        ib = Inbox(username=settings.REDDIT_USER, password=settings.REDDIT_PASSWORD)
        try:
            ib.send(to, subject, message)
        except (HTTPError, URLError), exc:
            logger.error("Error sending message, queueing for retry")
            self.retry([to, subject, message], kwargs=kwargs, exc=exc)
        except LoginError, exc:
            logger.error("Error logging into Reddit")


@task(ignore_result=True)
def process_validations():
    logger = process_validations.get_logger()
    try:
        inbox = Inbox(settings.REDDIT_USER, settings.REDDIT_PASSWORD)
    except (HTTPError, URLError), exc:
        logger.error("Error with Reddit, aborting.")
        return
    except LoginError, exc:
        logger.error("Error logging into Reddit")
        return 

    for msg in inbox:
        if not msg.was_comment:
            try:
                acc = RedditAccount.objects.get(username__iexact=msg.author)
                if not acc.validated and msg.subject == "Validation: %s" % acc.user.username:
                    logger.info("Validated %s" % acc.user.username)
                    acc.validated = True
                    acc.save()
            except RedditAccount.DoesNotExist:
                continue

