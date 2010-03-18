from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.auth.views import login
import django_cron
import settings

from registration.views import register
from registration.forms import RegistrationFormUniqueEmail

django_cron.autodiscover()
admin.autodiscover()

urlpatterns = patterns('',
    (r'^register/$', register, {'form_class' :RegistrationFormUniqueEmail }),
    (r'^admin/', include(admin.site.urls)),
    ('', include('registration.urls')),
    ('', include('sso.urls')),
    (r'^eveapi/', include('eve_proxy.urls')),
    (r'^api/', include('api.urls')),
)

urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)
