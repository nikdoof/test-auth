import re
from datetime import datetime

from django.db import models
from django.template.loader import render_to_string

from eve_api.models import EVEPlayerCharacter
from hr.app_defines import *
from hr.models import Blacklist, Application

def installed(value):
    from django.conf import settings
    apps = settings.INSTALLED_APPS
    if "." in value:
        for app in apps:
            if app == value:
                return True
    else:
        for app in apps:
            fields = app.split(".")
            if fields[-1] == value:
                return True
    return False


def blacklist_values(user, level=BLACKLIST_LEVEL_NOTE):
    """
    Returns a list of blacklist values that apply to the application
    """

    blacklist = []
    bl_items = Blacklist.objects.filter(models.Q(expiry_date__gt=datetime.now()) | models.Q(expiry_date=None), level__lte=level)

    # Check Reddit blacklists
    if installed('reddit'):
        reddit_uids = user.redditaccount_set.all().values_list('username', flat=True)
        objs = bl_items.filter(type=BLACKLIST_TYPE_REDDIT, value__in=reddit_uids)
        blacklist.extend(objs)

    # Check email blacklists
    blacklist.extend(bl_items.filter(type=BLACKLIST_TYPE_EMAIL, value=user.email.lower()))

    # Check Auth blacklists
    blacklist.extend(bl_items.filter(type=BLACKLIST_TYPE_AUTH, value=user.username.lower()))

    # Check EVE Related blacklists
    evechars = EVEPlayerCharacter.objects.filter(eveaccount__user=user).distinct().select_related('corporation', 'corporation__alliance')

    # Check Character blacklists
    characters = [re.escape(x) for x in evechars.values_list('name', flat=True) if x]
    if len(characters):
        objs = bl_items.filter(type=BLACKLIST_TYPE_CHARACTER, value__iregex=r'^(' + '|'.join(characters) + ')$')
        blacklist.extend(objs)

    # Check Corporation blacklists
    corporations = set([re.escape(x) for x in evechars.values_list('corporation__name', flat=True) if x])
    if len(corporations):
        objs = bl_items.filter(type=BLACKLIST_TYPE_CORPORATION, value__iregex=r'^(' + '|'.join(corporations) + ')$')
        blacklist.extend(objs)

    # Check Alliance blacklists
    alliances = set([re.escape(x) for x in evechars.values_list('corporation__alliance__name', flat=True) if x])
    if len(alliances):
        objs = bl_items.filter(type=BLACKLIST_TYPE_ALLIANCE, value__iregex=r'^(' + '|'.join([x for x in alliances if x]) + ')$')
        blacklist.extend(objs)

    # Check API Key blacklists
    keys = user.eveaccount_set.all().values_list('api_user_id', flat=True)
    objs = bl_items.filter(type=BLACKLIST_TYPE_APIUSERID, value__in=keys)
    blacklist.extend(objs)

    return blacklist

def recommendation_chain(application, first=True):
    """ Returns the recommendation chain for a application (as a nested dict) """

    output = {}
    for rec in Recommendation.objects.filter(user__username=name):
        # Avoid infinite loops
        if not rec.user == rec.recommended_user:
            output[rec.recommended_user.username] = recommendation_chain(rec.recommended_user.username, False)
    if first:
        return {name: output}
    return output

def check_permissions(user, application=None):
    """ Check if the user has permissions to view or admin the application """

    corplist = EVEPlayerCharacter.objects.select_related('roles').filter(eveaccount__user=user)
    if not application:
        if user.has_perm('hr.can_view_all') or user.has_perm('hr.can_view_corp') or corplist.filter(roles__name='roleDirector').count():
            return HR_ADMIN
    else:
        if application.user == user:
            return HR_VIEWONLY
        if user.has_perm('hr.can_view_all'):
            return HR_ADMIN
        else:
            # Give admin access to directors of the corp
            if application.corporation.id in corplist.filter(roles__name='roleDirector').values_list('corporation__id', flat=True):
                return HR_ADMIN

            # Give access to none director HR people access
            if application.corporation.id in corplist.values_list('corporation__id', flat=True) and user.has_perm('hr.can_view_corp'):
                return HR_ADMIN

    return HR_NONE

def send_message(application, message_type, note=None):
    from django.core.mail import send_mail
    subject = render_to_string('hr/emails/%s_subject.txt' % message_type, { 'app': application })
    subject = ''.join(subject.splitlines())
    message = render_to_string('hr/emails/%s.txt' % message_type, { 'app': application, 'note': note })
    try:
        send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', 'auth@nowhere.com'), [application.user.email])
    except:
        pass

    if installed('reddit') and len(application.user.redditaccount_set.all()) > 0:
            from reddit.tasks import send_reddit_message

            for account in application.user.redditaccount_set.all():
                send_reddit_message.delay(to=account.username, subject=subject, message=message)
