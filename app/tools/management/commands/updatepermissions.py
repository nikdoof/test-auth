from django.core.management.base import NoArgsCommand
from django.contrib.auth.management import create_permissions
from django.db.models import get_apps

class Command(NoArgsCommand):
    help = "Updates the application permissions stored in the DB"

    def handle_noargs(self, **options):
        for app in get_apps():
            create_permissions(app, None, 2)

