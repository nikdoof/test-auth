from celery.decorators import task
from reddit.api import Inbox
import settings

@task(ignore_result=True)
def send_reddit_message(to, subject, message):
    ib = Inbox(username=settings.REDDIT_USER, password=settings.REDDIT_PASSWORD)
    ib.send(to, subject, message)

