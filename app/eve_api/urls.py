from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse

from eve_api import views

urlpatterns = patterns('',
    url(r'^eveapi/add/', views.eveapi_add, name="eveapi-add"),
    url(r'^eveapi/delete/(?P<userid>\d+)/$', views.eveapi_del, name="eveapi-delete"),
    url(r'^eveapi/refresh/(?P<userid>\d+)/$', views.eveapi_refresh, name="eveapi-refresh"),
    url(r'^eveapi/log/(?P<userid>\d+)/$', views.eveapi_log, name="eveapi-log"),

    url(r'^character/list/$', views.eveapi_character, name="eveapi-characters-list"),
    url(r'^character/(?P<charid>\d+)/$', views.eveapi_character, name="eveapi-character"),

    url(r'^corporation/(?P<corporationid>\d+)/$', views.eveapi_corporation, name="eveapi-corporation"),

)
