from hr.app_defines import *
from hr.models import Blacklist

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
    evechars = EVEPlayerCharacter.objects.filter(eveaccount__user=user).select_related('corporation__alliance')

    # Check Character blacklists
    characters = evechars.values_list('name', flat=True)
    objs = bl_items.filter(type=BLACKLIST_TYPE_CHARACTER, value__in=characters)
    blacklist.extend(objs)

    # Check Corporation blacklists
    corporations = evechars.values_list('corporation__name', flat=True)
    objs = bl_items.filter(type=BLACKLIST_TYPE_CORPORATION, value__in=corporations)
    blacklist.extend(objs)

    # Check Alliance blacklists
    alliances = evechars.values_list('corporation__alliance__name', flat=True)
    objs = bl_items.filter(type=BLACKLIST_TYPE_ALLIANCE, value__in=alliances)
    blacklist.extend(objs)

    # Check API Key blacklists
    keys = user.eveaccount_set.all().values_list('api_user_id', flat=True)
    objs = bl_items.filter(type=BLACKLIST_TYPE_APIUSERID, value__in=keys)
    blacklist.extend(objs)

    return blacklist

