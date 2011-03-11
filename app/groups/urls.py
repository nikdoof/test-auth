from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from groups import views

urlpatterns = patterns('',
    (r'^list/$', views.group_list),
    (r'^request/(?P<groupid>\d+)/$', views.create_request),
    (r'^kick/(?P<groupid>\d+)/(?P<userid>\d+)/$', views.kick_member),
    (r'^promote/(?P<groupid>\d+)/(?P<userid>\d+)/$', views.promote_member),

    (r'^admin/(?P<groupid>\d+)/$', views.admin_group),
    (r'^accept/(?P<requestid>\d+)/$', views.accept_request),
    (r'^reject/(?P<requestid>\d+)/$', views.reject_request),
)

urlpatterns += patterns('django.views.generic.simple',
    ('^$', 'redirect_to', {'url': reverse('groups.views.group_list')}),
)
