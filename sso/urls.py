from django.conf.urls.defaults import *

from sso import views

urlpatterns = patterns('',
    ('^$', views.index),
    (r'^profile/$', views.profile),
    (r'^profile/add/eveapi', views.eveapi_add),
    (r'^profile/del/eveapi/$', views.eveapi_del),
    (r'^profile/del/eveapi/(?P<userid>\d+)/$', views.eveapi_del),
    (r'^profile/add/service', views.service_add),
    (r'^profile/del/service/$', views.service_del),
    (r'^profile/del/service/(?P<serviceid>\d+)/$', views.service_del),
    (r'^profile/reset/service/(?P<serviceid>\d+)/$', views.service_reset),
    (r'^profile/reset/service/(?P<serviceid>\d+)/(?P<accept>\d+)$', views.service_reset),
    (r'^profile/add/reddit', views.reddit_add),
    (r'^profile/del/reddit/$', views.reddit_del),
    (r'^profile/del/reddit/(?P<redditid>\d+)/$', views.reddit_del),
    (r'^profile/refresh/eveapi/(?P<userid>\d+)/$', views.eveapi_refresh),
    (r'^profile/log/eveapi/(?P<userid>\d+)/$', views.eveapi_log),
    (r'^profile/characters$', views.characters),
    (r'^profile/characters/(?P<charid>.*)/$', views.characters),
    (r'^profile/apipassword/', views.set_apipasswd),
    (r'^users/(?P<username>.*)/$', views.user_view),
    (r'^users/$', views.user_lookup),
)
