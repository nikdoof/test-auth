from django.conf.urls.defaults import *

from sso import views

urlpatterns = patterns('',
    ('^$', views.index),
    (r'^profile/$', views.profile),
    (r'^profile/add/eveapi', views.eveapi_add),
    (r'^profile/del/eveapi/$', views.eveapi_del),
    (r'^profile/del/eveapi/(?P<userid>\d+)/$', views.eveapi_del),
    (r'^profile/add/service', views.service_add),
    (r'^profile/del/service/$', views.eveapi_del),
    (r'^profile/del/service/(?P<serviceid>\d+)/$', views.service_del),
)
