import logging

from celery.signals import task_failure
from celery.decorators import task
from sentry.client.handlers import SentryHandler
from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerAlliance
from sso.models import ServiceAccount
from django.contrib.auth.models import User
from django.db.models import signals
from utils import installed

# Add Sentry error logging for Celery
logger = logging.getLogger('task')
logger.addHandler(SentryHandler())
def process_failure_signal(exception, traceback, sender, task_id, signal, args, kwargs, einfo, **kw):
    exc_info = (type(exception), exception, traceback)
    logger.error('Celery job exception: %s(%s)' % (exception.__class__.__name__, exception), exc_info=exc_info,
        extra={'data': {'task_id': task_id, 'sender': sender, 'args': args, 'kwargs': kwargs, }})
task_failure.connect(process_failure_signal)

# Signals that the tasks need to listen for
def eveapi_deleted(sender, instance, **kwargs):
    if instance.user:
        update_user_access.delay(user=instance.user.id)

signals.post_delete.connect(eveapi_deleted, sender=EVEAccount)


@task()
def update_user_access(user, **kwargs):
    """
    Process all corporate and alliance entries and correct
    access groups.
    """

    user = User.objects.get(id=user)

    # Create a list of all Corp and Alliance groups
    corpgroups = []
    for corp in EVEPlayerCorporation.objects.filter(group__isnull=False):
        if corp.group:
            corpgroups.append(corp.group)
    for alliance in EVEPlayerAlliance.objects.filter(group__isnull=False):
        if alliance.group:
            corpgroups.append(alliance.group)

    # Create a list of Char groups
    chargroups = []
    for eacc in EVEAccount.objects.filter(user=user):
        if eacc.api_status in [1, 3]:
            for char in eacc.characters.all():
                if char.corporation.group:
                    chargroups.append(char.corporation.group)
                if char.corporation.alliance and char.corporation.alliance.group:
                        chargroups.append(char.corporation.alliance.group)

    # Generate the list of groups to add/remove
    delgroups = set(set(user.groups.all()) & set(corpgroups)) - set(chargroups)
    addgroups = set(chargroups) - set(set(user.groups.all()) & set(corpgroups))

    # Check that user's groups fufil requirements
    if installed('groups'):
        for g in user.groups.filter(groupinformation__parent__isnull=False):
            print g
            if not g in delgroups and not g.groupinformation.parent in user.groups.all():
                delgroups.add(g)

    for g in delgroups:
        if g in user.groups.all():
            user.groups.remove(g)

    for g in addgroups:
        if not g in user.groups.all():
            user.groups.add(g)

    # For users set to not active, delete all accounts
    if not user.is_active:
        for servacc in ServiceAccount.objects.filter(user=user):
            servacc.active = 0
            servacc.save()
            pass
    else:
        # For each of the user's services, check they're in a valid group for it and enable/disable as needed.
        for servacc in ServiceAccount.objects.filter(user=user):
            if not (set(user.groups.all()) & set(servacc.service.groups.all())):
                if servacc.active:
                    servacc.active = 0
                    servacc.save()
                    pass
            else:
                if not servacc.active:
                    servacc.active = 1
                    servacc.save()
                    pass

    update_service_groups.delay(user_id=user.id)


@task(ignore_result=True)
def update_service_groups(user_id):
    for service in ServiceAccount.objects.filter(user=user_id, active=True).select_related('service__api'):
        api = service.service.api_class
        try:
            print "Updating %s" % service
            api.update_groups(service.service_uid, service.user.groups.all(), service.character)
            print "Done"
        except:
            print "Error updating %s %s" % (service.service, service.service_uid)
            pass
