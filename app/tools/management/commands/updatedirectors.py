from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import Group, User
from eve_api.models import EVEPlayerCharacter
from sso.tasks import update_user_access

class Command(NoArgsCommand):
    help = "Updates the members of the alliance director group"

    def handle_noargs(self, **options):
        g = Group.objects.get(name="Alliance Directors")

        users = []
        for char in EVEPlayerCharacter.objects.filter(corporation__alliance__name="Test Alliance Please Ignore",roles__name="roleDirector"):
            if char.eveaccount_set.count() and char.eveaccount_set.all()[0].user and not (char.corporation.group and char.corporation.group.id in settings.IGNORE_CORP_GROUPS):
                users.append(char.eveaccount_set.all()[0].user)

        add = set(users) - set(g.user_set.all())
        rem = set(g.user_set.all()) - set(users)

        print g.user_set.all()

        for m in rem:
            m.groups.remove(g)
            update_user_access.delay(m.id)

        for m in add:
            m.groups.add(g)
            update_user_access.delay(m.id)
