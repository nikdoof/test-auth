from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.contrib.auth.views import password_change, password_change_done

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
    (r'^profile/refresh/(?P<userid>\d+)/', views.refresh_access),
    (r'^profile/change/password/$', password_change),
    (r'^profile/change/email/$', views.email_change),
    (r'^profile/change/primary/$', views.primarychar_change),
    (r'^profile/change/reddittag/$', views.toggle_reddit_tagging),
    (r'^users/(?P<username>.*)/$', views.user_view),
    (r'^users/$', views.user_lookup),
)

urlpatterns += patterns('django.views.generic.simple',
    ('^$', 'redirect_to', {'url': reverse('sso.views.profile')}),
)
