from common import *

## Database
DATABASES = {
    'default': {
        'NAME': 'dreddit_sso.db',
        'ENGINE': 'django.db.backends.sqlite3',
        'USER': '',
        'PASSWORD': '',
    },

}

## EVE Proxy

EVE_API_URL = "https://apitest.eveonline.com"
EVE_PROXY_KEEP_LOGS = 30

## SSO
DISABLE_SERVICES = False
GENERATE_SERVICE_PASSWORD = False
IGNORE_CORP_GROUPS = [29]

## Server Mail
SERVER_EMAIL = 'trace@auth.pleaseignore.com'
DEFAULT_FROM_EMAIL = "bot@auth.pleaseignore.com"

## Registration
ACCOUNT_ACTIVATION_DAYS = 14
BANNED_EMAIL_DOMAINS = ['att.net']

## Reddit 
REDDIT_USER = 'DredditVerification'
REDDIT_PASSWORD = ''

## HR 
HR_RECOMMENDATION_DAYS = 45

## API
FULL_API_USER_ID = 415631
FULL_API_CHARACTER_ID = 246102445

## Django
DEBUG = True
SECRET_KEY = '8i2+dd-b2tg9g%mq$&i$-8beh4i5^2mm=e-nh^$p47^w=z1igr'

ADMINS = (
     ('Andrew Williams', 'andy@tensixtyone.com'),
)
MANAGERS = ADMINS

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

