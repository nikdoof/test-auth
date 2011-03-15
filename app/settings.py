import os
import djcelery
from datetime import timedelta

# Django settings for login project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1','91.121.180.45')

ADMINS = (
     ('Andrew Williams', 'andy@tensixtyone.com'),
)

MANAGERS = ADMINS

# Import db settings from dbsettings.py
from conf.dbsettings import *

# Import the Broker settings
from conf.brokersettings import *

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '8i2+dd-b2tg9g%mq$&i$-8beh4i5^2mm=e-nh^$p47^w=z1igr'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'sso.middleware.IGBMiddleware',
    'sso.middleware.IPTrackingMiddleware',
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

## Server Mail
SERVER_EMAIL = 'trace@auth.pleaseignore.com'

# API OAuth
#OAUTH_AUTH_VIEW = 'api.views.oauth.authorize_oauth'
OAUTH_CALLBACK_VIEW = 'api.views.oauth_callback'

# Disable the service API, used for data imports
DISABLE_SERVICES = False

# Services API generates a new password for the user
GENERATE_SERVICE_PASSWORD = False

AUTHENTICATION_BACKENDS = (
    'sso.backends.SimpleHashModelBackend',
)


AUTH_PROFILE_MODULE = 'sso.SSOUser'
LOGIN_REDIRECT_URL = "/profile"
LOGIN_URL = "/login"

DEFAULT_FROM_EMAIL = "bot@auth.pleaseignore.com"
ACCOUNT_ACTIVATION_DAYS = 14

# Slice File Location
SLICE = os.path.join(os.path.dirname(os.path.abspath( __file__ )),'Murmur.ice')

### Reddit Settings

# Username to validate accounts from
REDDIT_USER = 'DredditVerification'

# Password for validatio account
REDDIT_PASSWORD = ''

### HR Settings

HR_RECOMMENDATION_DAYS = 45

FULL_API_USER_ID = 415631
FULL_API_CHARACTER_ID = 246102445

## Email Registration

BANNED_EMAIL_DOMAINS = ['att.net']


## Eve Proxy settings

EVE_PROXY_KEEP_LOGS = 30

# try and import local settings
try:
    from conf.settingslocal import *
except:
    pass

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
}

CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_RESULT_BACKEND = "amqp"
CELERY_DISABLE_RATE_LIMITS = True
CELERYD_PREFETCH_MULTIPLIER = 128
CELERY_ALWAYS_EAGER = DEBUG

# Load the Celery tasks
djcelery.setup_loader()
