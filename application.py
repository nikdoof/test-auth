import sys
import os
import django.core.handlers.wsgi

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))
os.environ['DJANGO_SETTINGS_MODULE'] = 'app.conf.production'
application = django.core.handlers.wsgi.WSGIHandler()
