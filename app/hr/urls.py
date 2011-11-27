from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

from hr import views

urlpatterns = patterns('',
    url('^$', login_required(views.HrIndexView.as_view()), name='hr-index'),

    url(r'^application/$', login_required(views.HrViewUserApplications.as_view()), name='hr-userapplications'),
    url(r'^application/(?P<slug>\d+)/$', login_required(views.HrViewApplication.as_view()), name='hr-viewapplication'),
    url(r'^application/(?P<slug>\d+)/update/(?P<status>\d+)/$', login_required(views.HrUpdateApplication.as_view()), name='hr-updateapplication'),
    url(r'^application/(?P<applicationid>\d+)/note/$', login_required(views.HrAddNote.as_view()), name='hr-addnote'),
    url(r'^application/(?P<applicationid>\d+)/message/$', login_required(views.HrAddMessage.as_view()), name='hr-addmessage'),
    url(r'^application/(?P<applicationid>\d+)/reject/$', login_required(views.HrRejectApplication.as_view()), name='hr-rejectapplication'),
    url(r'^application/(?P<applicationid>\d+)/accept/$', login_required(views.HrAcceptApplication.as_view()), name='hr-acceptapplication'),
    url(r'^application/add/$', login_required(views.HrAddApplication.as_view()), name='hr-addapplication'),
    url(r'^application/admin/$', login_required(views.HrAdminApplications.as_view()), name='hr-admin'),

    url(r'^recommendation/$', login_required(views.HrViewRecommendations.as_view()), name='hr-viewrecommendations'),
    url(r'^recommendation/add/$', login_required(views.HrAddRecommendation.as_view()), name='hr-addrecommendation'),

    url(r'^blacklist/$', login_required(views.HrBlacklistList.as_view()), name='hr-blacklist-list'),
    url(r'^blacklist/add/$', login_required(views.HrAddBlacklist.as_view()), name='hr-blacklist-add'),
    url(r'^blacklist/add/user/(?P<userid>\d+)/$', login_required(views.HrBlacklistUser.as_view()), name='hr-blacklistuser'),
)
