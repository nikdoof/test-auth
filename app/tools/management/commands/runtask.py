from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = ("Executes a Celery task")

    option_list = BaseCommand.option_list + (
        make_option('-t', '--task', action='store', dest='task', help='ID of the task'),
        make_option('-a', '--args', action='store', dest='args', help='Arguments to pass to the task'),
    )

    requires_model_validation = False

    def handle(self, **options):

        if not options.get('task', None):
            raise CommandError('You need to provide a task to run.')

        if options.get('args', None):
            raise CommandError('Passing arguments to tasks is not yet supported.')

        # Split the task name off the namespace, import, then grab the function
        modpath = ".".join(options.get('task').split(".")[:-1])
        try:
            mod = __import__(modpath)
        except ImportError:
            raise CommandError('Error importing task')

        for i in options.get('task').split(".")[1:]:
            mod = getattr(mod, i)

        if not options.get('args', None):
            print "Executing Task: %s.delay()" % options.get('task')
            mod.delay()
