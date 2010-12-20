from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.auth.views import login
from django.conf import settings

from utils import installed

from registration.views import register
from sso.forms import RegistrationFormUniqueEmailBlocked

admin.autodiscover()

urlpatterns = patterns('',
    (r'^register/$', register, {'form_class': RegistrationFormUniqueEmailBlocked}),
    (r'^admin/', include(admin.site.urls)),
    ('', include('registration.urls')),
    ('', include('sso.urls')),
    (r'^eveapi/', include('eve_proxy.urls')),
    (r'^api/', include('api.urls')),
    (r'^hr/', include('hr.urls')),
    (r'^groups/', include('groups.urls')),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)

if installed('reddit'):
    urlpatterns += patterns('',
        ('', include('sso.urls')),
    )

