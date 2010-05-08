from django.conf.urls.defaults import *

from hr import views

urlpatterns = patterns('',
    ('^$', views.index),
    (r'^recommendations/$', views.view_recommendations),
    (r'^recommendations/(?P<recommendationid>.*)/$', views.view_recommendation),
    (r'^applications/$', views.view_applications),
    (r'^applications/(?P<applicationid>\d+)/$', views.view_application),
    (r'^applications/(?P<applicationid>\d+)/update/(?P<status>\d+)/$', views.update_application),
    (r'^applications/(?P<applicationid>\d+)/note/$', views.add_note),
    (r'^applications/(?P<applicationid>\d+)/reject/$', views.reject_application),
    (r'^applications/(?P<applicationid>\d+)/accept/$', views.accept_application),

    (r'^add/application/$', views.add_application),
    (r'^add/recommendation/$', views.add_recommendation),

    (r'^admin/applications/$', views.admin_applications),
)
