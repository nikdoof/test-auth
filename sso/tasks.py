from celery.decorators import task
from eve_api.models import *

@task()
def update_user_access(user):
    """ Process all corporate and alliance entries and correct access groups """

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
        if eacc.api_status in [1,3]:
            for char in eacc.characters.all():
                if char.corporation.group:
                    chargroups.append(char.corporation.group)
                if char.corporation.alliance and char.corporation.alliance.group:
                        chargroups.append(char.corporation.alliance.group)

    # Generate the list of groups to add/remove
    delgroups = set(set(user.groups.all()) & set(corpgroups)) - set(chargroups)
    addgroups = set(chargroups) - set(set(user.groups.all()) & set(corpgroups))

    for g in delgroups:
        user.groups.remove(g)

    for g in addgroups:
        user.groups.add(g)

    from sso.models import ServiceAccount

    # For users set to not active, delete all accounts
    if not user.is_active:
        for servacc in ServiceAccount.objects.filter(user=user):
            servacc.active = 0
            servacc.save()
            pass

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
