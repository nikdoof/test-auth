import os
import djcelery

# Debug settings
DEBUG = False
TEMPLATE_DEBUG = True

# Zone Settings
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_TZ = True

# Defines the Static Media storage as per staticfiles contrib
STATIC_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'static')
STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sso.middleware.InactiveLogoutMiddleware',
    'sso.middleware.IGBMiddleware',
    'sso.middleware.IPTrackingMiddleware',
    'raven.contrib.django.middleware.Sentry404CatchMiddleware',
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), '..', 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request"
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'raven.contrib.django',
    'gargoyle',
    'south',
    'piston',
    'djcelery',
    'registration',
    'formtools',
    'eve_proxy',
    'eve_api',
    'reddit',
    'hr',
    'sso',
    'groups',
    'api',
    'tools',
]

AUTH_PROFILE_MODULE = 'sso.SSOUser'
LOGIN_REDIRECT_URL = "/profile"
LOGIN_URL = "/login"

### OAuth

OAUTH_AUTH_VIEW = 'api.views.oauth_auth_view'
OAUTH_CALLBACK_VIEW = 'api.views.oauth_callback_view'

## EVE Proxy

EVE_API_URL = "https://api.eveonline.com"
EVE_CDN_URL = "https://image.eveonline.com"
EVE_PROXY_KEEP_LOGS = 30

# Manual adjustments to cache timers (lowercase path)
EVE_PROXY_CACHE_ADJUSTMENTS = {
    '/api/calllist.xml.aspx': 3600,
}

### Celery Schedule

from celeryschedule import *

CELERY_DISABLE_RATE_LIMITS = True
CELERY_ALWAYS_EAGER = DEBUG
CELERY_EAGER_PROPAGATES_EXCEPTIONS = DEBUG
CELERYD_HIJACK_ROOT_LOGGER = False

# Load the Celery tasks
djcelery.setup_loader()

GARGOYLE_AUTO_CREATE = True

# Switches for Gargoyle
GARGOYLE_SWITCH_DEFAULTS = {
    'reddit': {
      'is_active': True,
      'label': 'Reddit Functionality',
      'description': 'Enables/Disables the Reddit integration for HR and SSO.',
    },
    'hr': {
      'is_active': True,
      'label': 'HR Functions',
      'description': 'Enables/Disables the HR functionality.',
    },
    'eve-cak': {
      'is_active': True,
      'label': 'EVE Customizable API Keys',
      'description': 'Enables/Disables EVE API CAK support.',
    },
    'eve-testapi': {
      'is_active': False,
      'label': 'EVE Test API Endpoints',
      'description': 'Use the Test API endpoints instead of Live.',
    },
    'eve-keydelete': {
      'is_active': False,
      'label': 'Allow EVE API Key Delete',
      'description': 'Allows API keys to be deleted by th end user.',
    },
    'api-disableprocessing': {
      'is_active': False,
      'label': 'Disable API Backend Processing',
      'description': 'Disables backend processing for the EVE API, stops Auth hammering the API during outages',
    },
    'eve-softkeydelete': {
      'is_active': False,
      'label': 'Soft API Key Deletions',
      'description': 'API Keys are not deleted from the database, only removed from the user.',
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}
