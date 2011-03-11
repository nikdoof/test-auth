from django.conf import settings
import logging
from datetime import datetime, timedelta
from celery.decorators import task
from hr.utils import blacklist_values
from django.contrib.auth.models import User
from django.core.mail import send_mail

@task(ignore_result=True)
def blacklist_check():
    log = blacklist_check.get_logger()

    users = User.objects.filter(is_active=True)

    for u in users:
        if u.groups.count() > 0:
            # Has groups
            val = blacklist_values(u)
            if len(val) > 0:
                # Report possible issue
                log.warning("Suspect User: %s, %s entries found: %s" % (u.username, len(val), val))

                blstr = ""
                for i in val:
                    blstr = "%s%s - %s - %s\n" % (blstr, i.get_type_display(), i.value, i.reason)
                msg = "Suspect User found: %s\nGroups: %s\nBlacklist Items:\n\n%s" % (u.username, u.groups.all(), blstr)
                send_mail('Automated blacklist checker alert - %s' % u.username, msg, 'blacklist@pleaseignore.com', ['abuse@pleaseignore.com'])
