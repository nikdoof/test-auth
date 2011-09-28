import sys
import logging
import urllib
import urllib2
from hashlib import sha512

from django.conf import settings
from django.db.models import signals
from django.utils import simplejson as json

from django.contrib.auth.models import User
from celery.signals import task_failure
from celery.decorators import task

from api.models import AuthAPIKey
from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerAlliance
from eve_api.app_defines import *
from sso.models import ServiceAccount, SSOUser
from reddit.tasks import update_user_flair
from utils import installed

# Add Sentry error logging for Celery
def process_failure_signal(exception, traceback, sender, task_id, signal, args, kwargs, einfo, **kw):
    exc_info = (type(exception), exception, traceback)
    logger = logging.getLogger('celery.task')
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

    logger = update_user_access.get_logger()
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
    for eacc in EVEAccount.objects.filter(user=user, api_status__in=[API_STATUS_OK, API_STATUS_OTHER_ERROR], api_keytype__in=getattr(settings, 'SSO_ACCEPTED_KEYTYPES', [API_KEYTYPE_LIMITED, API_KEYTYPE_FULL, API_KEYTYPE_ACCOUNT])):
        for char in eacc.characters.all():
            if char.corporation.group:
                chargroups.append(char.corporation.group)
            elif char.corporation.alliance and char.corporation.alliance.group:
                chargroups.append(char.corporation.alliance.group)

    # Generate the list of groups to add/remove
    delgroups = set(set(user.groups.all()) & set(corpgroups)) - set(chargroups)
    addgroups = set(chargroups) - set(set(user.groups.all()) & set(corpgroups))

    # Check that user's groups fufil requirements
    if installed('groups'):
        for g in user.groups.filter(groupinformation__parent__isnull=False):
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

    notifyurls = AuthAPIKey.objects.filter(active=True).exclude(callback='')
    if notifyurls.count():
        data = {'username': user.username, 'groups': list(user.groups.all().values('id', 'name'))}
        # Update remote services with poking the notification URLs
        for endpoint in notifyurls:
            url, key = endpoint.callback, endpoint.key
            jsonstr = json.dumps(data)
            hash = sha512('%s-%s' % (key, jsonstr)).hexdigest()
            req = urllib2.Request(url, urllib.urlencode({'data': jsonstr, 'auth': hash}))
            try:
                if sys.version_info < (2, 6):
                    conn = urllib2.urlopen(req)
                else:
                    conn = urllib2.urlopen(req, timeout=5)
            except (urllib2.HTTPError, urllib2.URLError) as e:
                logger.error('Error notifying SSO service: %s' % e.code, exc_info=sys.exc_info(), extra={'data': {'url': url}})
                pass

    update_service_groups.delay(user_id=user.id)


@task(ignore_result=True)
def update_service_groups(user_id):
    logger = update_service_groups.get_logger()
    for service in ServiceAccount.objects.filter(user=user_id, active=True).select_related('service__api'):
        api = service.service.api_class
        try:
            api.update_groups(service.service_uid, service.user.groups.all(), service.character)
            logger.debug("Service %s (%s) Updated" % (service.service, service.service_uid))
        except Exception as e:
            logger.error("Error updating Service %s (%s) - %s" % (service.service, service.service_uid, e), exc_info=sys.exc_info(), extra={'service': service.service, 'service_uid': service.service_uid})
            pass


@task(ignore_result=True)
def update_reddit_tag():
    for sobj in SSOUser.objects.filter(tag_reddit_accounts=True):
        if sobj.primary_character and sobj.user.redditaccount_set.count():
            for redditacc in sobj.user.redditaccount_set.all():
                update_user_flair.delay(redditacc.username, sobj.primary_character.name)
