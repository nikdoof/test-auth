from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse

from sso import views

urlpatterns = patterns('',
    ('^$', views.profile),
    (r'^profile/$', views.profile),
    (r'^profile/add/service', views.service_add),
    (r'^profile/del/service/$', views.service_del),
    (r'^profile/del/service/(?P<serviceid>\d+)/$', views.service_del),
    (r'^profile/reset/service/(?P<serviceid>\d+)/$', views.service_reset),
    (r'^profile/reset/service/(?P<serviceid>\d+)/(?P<accept>\d+)$', views.service_reset),
    (r'^profile/apipassword/', views.set_apipasswd),
    (r'^profile/refresh/', views.refresh_access),
    (r'^users/(?P<username>.*)/$', views.user_view),
    (r'^users/$', views.user_lookup),
)

urlpatterns += patterns('django.views.generic.simple',
    ('^$', 'redirect_to', {'url': reverse('sso.views.profile')}),
)
