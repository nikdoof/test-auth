from datetime import datetime
from hr.app_defines import *
from hr.models import Blacklist, Application
from django.db import models
from eve_api.models import EVEPlayerCharacter

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


def blacklist_values(user):
    """
    Returns a list of blacklist values that apply to the application
    """

    blacklist = []
    bl_items = Blacklist.objects.filter(models.Q(expiry_date__gt=datetime.now()) | models.Q(expiry_date=None))

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
    evechars = EVEPlayerCharacter.objects.filter(eveaccount__user=user).select_related('corporation', 'corporation__alliance')

    # Check Character blacklists
    characters = evechars.values_list('name', flat=True)
    objs = bl_items.filter(type=BLACKLIST_TYPE_CHARACTER, value__iregex=r'(' + '|'.join(characters) + ')')
    blacklist.extend(objs)

    # Check Corporation blacklists
    corporations = evechars.values_list('corporation__name', flat=True)
    objs = bl_items.filter(type=BLACKLIST_TYPE_CORPORATION, value__iregex=r'(' + '|'.join(corporations) + ')')
    blacklist.extend(objs)

    # Check Alliance blacklists
    alliances = evechars.values_list('corporation__alliance__name', flat=True)
    objs = bl_items.filter(type=BLACKLIST_TYPE_ALLIANCE, value__iregex=r'(' + '|'.join([x for x in alliances if x]) + ')')
    blacklist.extend(objs)

    # Check API Key blacklists
    keys = user.eveaccount_set.all().values_list('api_user_id', flat=True)
    objs = bl_items.filter(type=BLACKLIST_TYPE_APIUSERID, value__in=keys)
    blacklist.extend(objs)

    return blacklist

def recommendation_chain(application):
    """ Returns the recommendation chain for a application (as a nested dict) """

    t = {}
    for rec in application.recommendation_set.all():
        try:
            app = Application.objects.get(character=rec.user_character, status=APPLICATION_STATUS_COMPLETED)
            t[rec.user_character.name] = recommendation_chain(app)
        except Application.DoesNotExist:
            t[rec.user_character.name] = {}
    return t
