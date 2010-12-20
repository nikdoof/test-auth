from celery.decorators import task
from reddit.models import RedditAccount
from reddit.api import Inbox
from django.conf import settings

@task(ignore_result=True)
def send_reddit_message(to, subject, message):
    ib = Inbox(username=settings.REDDIT_USER, password=settings.REDDIT_PASSWORD)
    ib.send(to, subject, message)

@task(ignore_result=True)
def process_validations():
    log = process_validations.get_logger()
    inbox = Inbox(settings.REDDIT_USER, settings.REDDIT_PASSWORD)
    for msg in inbox:
        if not msg.was_comment:
            try:
                acc = RedditAccount.objects.get(username__iexact=msg.author)
                if not acc.validated and msg.subject == "Validation: %s" % acc.user.username:
                    log.info("Validated %s" % acc.user.username)
                    acc.validated = True
                    acc.save()
            except RedditAccount.DoesNotExist:
                continue

