from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.auth.views import login
from django.conf import settings

from utils import installed

from registration.views import register
from sso.forms import RegistrationFormUniqueEmailBlocked

admin.autodiscover()

urlpatterns = patterns('',
    ('', include('registration.backends.default.urls')),
    (r'^register/$', register, {'backend': 'registration.backends.default.DefaultBackend', 'form_class': RegistrationFormUniqueEmailBlocked}),
    (r'^admin/', include(admin.site.urls)),
    ('', include('sso.urls')),
    (r'^eve/', include('eve_api.urls')),
    (r'^eveapi/', include('eve_proxy.urls')),
    (r'^api/', include('api.urls')),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
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

