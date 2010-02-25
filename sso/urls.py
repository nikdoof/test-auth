from django.conf.urls.defaults import *

from sso import views

urlpatterns = patterns('',
    (r'^profile/', views.profile),
)
