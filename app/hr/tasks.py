from django.conf import settings
import logging
from datetime import datetime, timedelta

from celery.task import task

from hr.utils import blacklist_values
from django.contrib.auth.models import User
from django.core.mail import send_mail

@task(ignore_result=True)
def blacklist_check():
    log = blacklist_check.get_logger()

    users = User.objects.filter(is_active=True)

    alerts = 0
    msg = ""

    for u in users:
        if u.groups.count() > 0:
            # Has groups
            val = blacklist_values(u)
            if len(val) > 0:
                alerts += 1
                # Report possible issue
                log.warning("Suspect User: %s, %s entries found: %s" % (u.username, len(val), val))

                blstr = ""
                for i in val:
                    blstr = "%s%s - %s - %s\n" % (blstr, i.get_type_display(), i.value, i.reason)

                msg += "\n\n-----\n\n"
                msg += "Suspect User found: %s\nGroups: %s\nBlacklist Items:\n\n%s" % (u.username, ", ".join(u.groups.all().values_list('name', flat=True)), blstr)

    if alerts:
        send_mail('Automated blacklist checker alerts', msg, 'blacklist@pleaseignore.com', ['abuse@pleaseignore.com'])
