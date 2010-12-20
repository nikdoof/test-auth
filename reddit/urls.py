
from django.conf.urls.defaults import *

from sso import views

urlpatterns = patterns('',
    (r'^profile/add/reddit', views.reddit_add),
    (r'^profile/del/reddit/$', views.reddit_del),
    (r'^profile/del/reddit/(?P<redditid>\d+)/$', views.reddit_del),
)

