from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.auth.views import login
import django_cron
import settings

django_cron.autodiscover()
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    ('', include('registration.urls')),
    ('', include('sso.urls')),
    (r'^eveapi/', include('eve_proxy.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
