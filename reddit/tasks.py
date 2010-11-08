from celery.decorators import task
from reddit.api import Inbox
import settings

@task(ignore_result=True)
def send_reddit_message(to, subject, message):
    ib = Inbox(settings.REDDIT_USER, settings.REDDIT_PASSWORD)
    ib.send(to, subject, message)

