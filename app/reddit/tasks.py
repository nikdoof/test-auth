from datetime import datetime, timedelta
from urllib2 import HTTPError, URLError

from django.conf import settings
from django.utils.timezone import now

from celery.task import Task, task

from reddit.models import RedditAccount
from reddit.api import Inbox, LoginError, Flair


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
    log.info("Updating Accounts older than %s" % (now() - delta))
    accounts = RedditAccount.objects.order_by('last_update').filter(last_update__lt=(now() - delta))[:batch_size]
    log.info("%s account(s) to update" % accounts.count())
    for acc in accounts:
        log.debug("Queueing Account %s for update" % acc.username)
        if not acc.user:
            acc.delete()
            continue
        update_account.delay(username=acc.pk)


class update_user_flair(Task):
    """
    Updates a user's flair on Reddit
    """

    default_retry_delay = 5 * 60 # retry in 5 minutes
    ignore_result = True

    def run(self, username, character_name, **kwargs):
        try:
            ib = Flair(username=settings.REDDIT_USER, password=settings.REDDIT_PASSWORD)
            ib.set_flair(settings.REDDIT_SUBREDDIT, username, character_name, '')
        except (HTTPError, URLError), exc:
            logger.error("Error updating flair, queueing for retry")
            update_user_flair.retry(args=[username, character_name], kwargs=kwargs, exc=exc)
            pass
        except LoginError, exc:
            logger.error("Error logging into Reddit")

