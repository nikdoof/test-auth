from django.conf.urls.defaults import *

from groups import views

urlpatterns = patterns('',
    ('^$', views.index),
    (r'^list/$', views.group_list),
    (r'^request/(?P<groupid>\d+)/$', views.create_request),
)
