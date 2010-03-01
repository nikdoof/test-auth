import os

# Django settings for login project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'dreddit_sso'             # Or path to database file if using sqlite3.
DATABASE_USER = 'dreddit_sso'             # Not used with sqlite3.
DATABASE_PASSWORD = 'bf6431670c657b9b62f08353d61047c4552ed3d4'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

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
MEDIA_ROOT = '/home/dreddit/www/auth.dredd.it/auth/media'

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
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), "templates"),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'registration',
    'django_cron',
    'eve_proxy',
    'eve_api',
#    'mumble',
    'sso',
)

AUTH_PROFILE_MODULE = 'sso.SSOUser'

LOGIN_REDIRECT_URL = "/profile"

### EVE Corp Info

ALLOWED_CORPS = [1018389948]

### Jabber Service Settings

# Vhost to add users to 
JABBER_SERVER = 'dredd.it'

# Group to add authed people to
JABBER_GROUP = 'dreddit'

# Use sudo?
JABBER_SUDO = True

### Mumble Service Settings

DEFAULT_CONN = 'Meta:tcp -h 127.0.0.1 -p 6502'
MUMBLE_DEFAULT_PORT = 64738
SLICE = '/usr/share/slice/Murmur.ice'

FORCE_SCRIPT_NAME=""
DEFAULT_FROM_EMAIL = "bot@auth.dredd.it"

ACCOUNT_ACTIVATION_DAYS = 14
