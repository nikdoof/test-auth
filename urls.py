from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #(r'^login/', include('django.contrib.auth.views.login')),

    (r'^admin/', include(admin.site.urls)),
)
