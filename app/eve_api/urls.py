from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from eve_api import views

urlpatterns = patterns('',
    url(r'^eveapi/add/$', views.EVEAPICreateView.as_view(), name="eveapi-add"),
    url(r'^eveapi/update/(?P<pk>\d+)/$', views.EVEAPIUpdateView.as_view(), name="eveapi-update"),
    url(r'^eveapi/delete/(?P<pk>\d+)/$', views.EVEAPIDeleteView.as_view(), name="eveapi-delete"),
    url(r'^eveapi/refresh/(?P<pk>\d+)/$', views.EVEAPIRefreshView.as_view(), name="eveapi-refresh"),
    url(r'^eveapi/log/(?P<userid>\d+)/$', views.EVEAPILogView.as_view(), name="eveapi-log"),
    url(r'^eveapi/access/(?P<pk>\d+)/$', views.EVEAPIAccessView.as_view(), name="eveapi-accessview"),

    url(r'^character/list/$', views.EVEAPICharacterListView.as_view(), name="eveapi-characters-list"),
    url(r'^character/(?P<pk>\d+)/$', views.EVEAPICharacterDetailView.as_view(), name="eveapi-character"),

    url(r'^corporation/(?P<pk>\d+)/$', views.EVEAPICorporationView.as_view(), name="eveapi-corporation"),
    url(r'^corporation/(?P<pk>\d+)/export/$', views.EVEAPICorporationMembersCSV.as_view(), name="eveapi-corporation-members-csv"),

    url(r'^alliance/(?P<pk>\d+)/$', views.EVEAPIAllianceView.as_view(), name="eveapi-alliance"),
)

try:
    import sso.views as ssoviews
except ImportError:
    pass
else:
    urlpatterns += patterns('',
        url(r'^corporation/(?P<corpid>\d+)/refresh/$', ssoviews.refresh_access, name='eveapi-corporation-refresh'),
        url(r'^alliance/(?P<allianceid>\d+)/refresh/$', ssoviews.refresh_access, name='eveapi-alliance-refresh'),
    )

