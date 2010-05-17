from django.conf.urls.defaults import *

from hr import views

urlpatterns = patterns('',
    ('^$', views.index),
    (r'^recommendation/$', views.view_recommendations),
    (r'^recommendation/(?P<recommendationid>.*)/$', views.view_recommendation),
    (r'^application/$', views.view_applications),
    (r'^application/(?P<applicationid>\d+)/$', views.view_application),
    (r'^application/(?P<applicationid>\d+)/update/(?P<status>\d+)/$', views.update_application),
    (r'^application/(?P<applicationid>\d+)/note/$', views.add_note),
    (r'^application/(?P<applicationid>\d+)/reject/$', views.reject_application),
    (r'^application/(?P<applicationid>\d+)/accept/$', views.accept_application),

    (r'^application/add/$', views.add_application),
    (r'^recommendation/add/$', views.add_recommendation),

    (r'^application/admin$', views.admin_applications),
)
