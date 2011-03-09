from django.conf import settings
import logging
from datetime import datetime, timedelta
from celery.decorators import task
from hr.utils import blacklist_values
from django.contrib.auth.models import User

@task(ignore_result=True)
def blacklist_check():
    log = blacklist_check.get_logger()

    users = User.objects.filter(active=True)

    for u in users:
        if users.groups.count() > 0:
            # Has groups
            val = blacklist_values(user)
            if len(val) > 0:
                # Report possible issue
                log.warn("Suspect User: %s, %s entries found" % (u.username, len(val)))
