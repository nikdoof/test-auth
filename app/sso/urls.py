from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth.views import password_change, password_change_done
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView

from sso import views

urlpatterns = patterns('',
    url('^$', RedirectView.as_view(url=reverse_lazy('sso-profile'))),
    url(r'^profile/$', views.ProfileView.as_view(), name='sso-profile'),
    (r'^profile/add/service', views.service_add),
    (r'^profile/del/service/$', views.service_del),
    (r'^profile/del/service/(?P<serviceid>\d+)/$', views.service_del),
    (r'^profile/reset/service/(?P<serviceid>\d+)/$', views.service_reset),
    (r'^profile/reset/service/(?P<serviceid>\d+)/(?P<accept>\d+)$', views.service_reset),
    url(r'^profile/apipassword/', views.APIPasswordUpdateView.as_view(), name='sso-apipassword'),
    (r'^profile/refresh/$', views.refresh_access),
    url(r'^profile/refresh/(?P<userid>\d+)/$', views.refresh_access, name='sso-refreshaccess'),
    (r'^profile/change/password/$', password_change),
    url(r'^profile/change/email/$', views.EmailUpdateView.as_view(), name='sso-emailupdate'),
    url(r'^profile/change/primary/$', views.PrimaryCharacterUpdateView.as_view(), name='sso-primarycharacterupdate'),
    url(r'^profile/change/reddittag/$', views.RedditTaggingUpdateView.as_view(), name='sso-reddittagging'),
    (r'^users/$', views.user_lookup),
    url(r'^users/(?P<username>.*)/addnote/$', views.AddUserNote.as_view(), name='sso-addusernote'),
    url(r'^users/(?P<username>.*)/$', views.UserDetailView.as_view(), name='sso-viewuser'),

    url(r'^address/$', views.UserIPAddressView.as_view(), name='sso-ipaddress'),
)

