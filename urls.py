from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

# Unregister unneeded interfaces
from eve_proxy.models import CachedDocument
admin.site.unregister(CachedDocument)

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    ('', include('registration.backends.default.urls')),
    ('', include('sso.urls')),
)
