from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.auth.views import login
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings


from utils import installed
from registration.views import register
from sso.forms import RegistrationFormUniqueEmailBlocked

admin.autodiscover()

urlpatterns = patterns('',
    ('', include('registration.backends.default.urls')),
    (r'^register/$', register, {'backend': 'registration.backends.default.DefaultBackend', 'form_class': RegistrationFormUniqueEmailBlocked}),
    ('', include('sso.urls')),
    (r'^eve/', include('eve_api.urls')),
    (r'^eveapi/', include('eve_proxy.urls')),
    (r'^api/', include('api.urls')),
)

if installed('reddit'):
    urlpatterns += patterns('',
        ('', include('reddit.urls')),
    )

if installed('hr'):
    urlpatterns += patterns('',
        (r'^hr/', include('hr.urls')),
    )

if installed('groups'):    
    urlpatterns += patterns('',
        (r'^groups/', include('groups.urls')),
    )

if installed('sentry'):
    urlpatterns += patterns('',
        (r'^sentry/', include('sentry.web.urls')),
    )

if installed('nexus'):
    import nexus
    nexus.autodiscover()

    urlpatterns += patterns('',
        (r'^nexus/', include(nexus.site.urls)),
    )

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
