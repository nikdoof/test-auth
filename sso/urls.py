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
    (r'^users/(?P<user>.*)/$', views.user_view),
    (r'^users/$', views.user_view),
)
