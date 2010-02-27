from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.auth.views import login
import settings

admin.autodiscover()

# Unregister unneeded interfaces
from eve_proxy.models import CachedDocument
admin.site.unregister(CachedDocument)

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    ('', include('registration.urls')),
    ('', include('sso.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
