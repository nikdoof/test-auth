from datetime import datetime, timedelta
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
        try:
            ib = Inbox(username=settings.REDDIT_USER, password=settings.REDDIT_PASSWORD)
            ib.send(to, subject, message)
        except (HTTPError, URLError), exc:
            logger.error("Error sending message, queueing for retry")
            send_reddit_message.retry(args=[to, subject, message], kwargs=kwargs, exc=exc)
            pass
        except LoginError, exc:
            logger.error("Error logging into Reddit")


@task(ignore_result=True)
def process_validations():
    logger = process_validations.get_logger()
    try:
        inbox = Inbox(settings.REDDIT_USER, settings.REDDIT_PASSWORD)
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
    except (HTTPError, URLError), exc:
        logger.error("Error with Reddit, aborting.")
        return
    except LoginError, exc:
        logger.error("Error logging into Reddit")
        return 


@task(ignore_result=True)
def update_account(username):

    logger = process_validations.get_logger()

    try:
        acc = RedditAccount.objects.get(pk=username)
        acc.api_update()
    except RedditAccount.DoesNotExist:
        pass
    else:
        acc.save()


@task(ignore_result=True, expires=120)
def queue_account_updates(update_delay=604800, batch_size=50):
    """
    Updates all Reddit accounts in the system
    """

    log = queue_account_updates.get_logger()
    # Update all the eve accounts and related corps
    delta = timedelta(seconds=update_delay)
    log.info("Updating Accounts older than %s" % (datetime.now() - delta))
    accounts = RedditAccount.objects.filter(last_updated_lt=(datetime.now() - delta))
    log.info("%s account(s) to update" % accounts.count())
    for acc in accounts:
        log.debug("Queueing Account %s for update" % acc.username)
        if not acc.user:
            acc.delete()
            continue
        update_account.delay(username=acc.pk)

