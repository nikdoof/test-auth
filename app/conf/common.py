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

# Defines the Static Media storage as per staticfiles contrib
STATIC_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'static')
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
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sso.middleware.InactiveLogoutMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'sso.middleware.IGBMiddleware',
    'sso.middleware.IPTrackingMiddleware',
)

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

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'nexus',
    'gargoyle',
    'sentry',
    'sentry.client',
    'south',
    'piston',
    'djcelery',
    'registration',
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

### OAuth

OAUTH_AUTH_VIEW = 'api.views.oauth_auth_view'
OAUTH_CALLBACK_VIEW = 'api.views.oauth_callback_view'

### Celery Schedule

from celeryschedule import *

CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_RESULT_BACKEND = "amqp"
CELERY_DISABLE_RATE_LIMITS = True
CELERYD_PREFETCH_MULTIPLIER = 128
CELERY_ALWAYS_EAGER = DEBUG
CELERY_EAGER_PROPAGATES_EXCEPTIONS = DEBUG

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
      'is_active': False,
      'label': 'EVE Customizable API Keys',
      'description': 'Enables/Disables EVE API CAK support.',
    },
    'eve-testapi': {
      'is_active': False,
      'label': 'EVE Test API Endpoints',
      'description': 'Use the Test API endpoints instead of Live.',
    },
    'api-disableprocessing': {
      'is_active': False,
      'label': 'Disable API Backend Processing',
      'description': 'Disables backend processing for the EVE API, stops Auth hammering the API during outages',
    }

}
