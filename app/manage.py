#!/usr/bin/env python
import sys
import os.path

pwd = os.path.dirname(os.path.abspath(__file__))
activate_this = os.path.join(pwd,'..', 'env','bin','activate_this.py')
try:
    execfile(activate_this, dict(__file__=activate_this))
except IOError:
    sys.stderr.write('Error activating virtualenv\n')
    sys.exit(1)

from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
