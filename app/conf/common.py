import os
import djcelery
from datetime import timedelta

# Django settings for login project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1','91.121.180.45')

ADMINS = (
     ('Andrew Williams', 'andy@tensixtyone.com'),
)

MANAGERS = ADMINS

# Zone Settings
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True

# Defines the Static Media storage as per staticfiles contrib
STATIC_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sso.middleware.InactiveLogoutMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'sso.middleware.IGBMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), "templates"),
)

TEMPLATE_CONTEXT_PRCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.contrib.staticfiles.context_processors.staticfiles",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request"
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'south',
    'piston',
    'djcelery',
    'registration',
    'debug_toolbar',
    'pagination',
    'eve_proxy',
    'eve_api',
    'reddit',
    'hr',
    'sso',
    'groups',
    'api',
    'tools',
)

AUTHENTICATION_BACKENDS = (
    'sso.backends.SimpleHashModelBackend',
)

AUTH_PROFILE_MODULE = 'sso.SSOUser'
LOGIN_REDIRECT_URL = "/profile"
LOGIN_URL = "/login"

### Celery Schedule

CELERYBEAT_SCHEDULE = {
    "reddit-validations": {
        "task": "reddit.tasks.process_validations",
        "schedule": timedelta(minutes=10),
    },
    "eveapi-update": {
        "task": "eve_api.tasks.account.queue_apikey_updates",
        "schedule": timedelta(minutes=10),
    },
    "alliance-update": {
        "task": "eve_api.tasks.alliance.import_alliance_details",
        "schedule": timedelta(hours=6),
    },
    "api-log-clear": {
        "task": "eve_proxy.tasks.clear_old_logs",
        "schedule": timedelta(days=1),
    },
    "blacklist-check": {
        "task": "hr.tasks.blacklist_check",
        "schedule": timedelta(days=1),
    },
    "reddit-update": {
        "task": "reddit.tasks.queue_account_updates",
        "schedule": timedelta(minutes=15),
    }
}

CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_RESULT_BACKEND = "amqp"
CELERY_DISABLE_RATE_LIMITS = True
CELERYD_PREFETCH_MULTIPLIER = 128
CELERY_ALWAYS_EAGER = DEBUG
CELERY_EAGER_PROPAGATES_EXCEPTIONS = DEBUG

# Load the Celery tasks
djcelery.setup_loader()