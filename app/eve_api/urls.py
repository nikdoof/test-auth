from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from eve_api import views

urlpatterns = patterns('',
    url(r'^eveapi/add/$', views.eveapi_add, name="eveapi-add"),
    url(r'^eveapi/update/(?P<userid>\d+)/$', views.eveapi_update, name="eveapi-update"),
    url(r'^eveapi/delete/(?P<pk>\d+)/$', login_required(views.EVEAPIDeleteView.as_view()), name="eveapi-delete"),
    url(r'^eveapi/refresh/(?P<pk>\d+)/$', login_required(views.EVEAPIRefreshView.as_view()), name="eveapi-refresh"),
    url(r'^eveapi/log/(?P<userid>\d+)/$', login_required(views.EVEAPILogView.as_view()), name="eveapi-log"),
    url(r'^eveapi/access/(?P<slug>\d+)/$', login_required(views.EVEAPIAccessView.as_view()), name="eveapi-accessview"),

    url(r'^character/list/$', login_required(views.EVEAPICharacterListView.as_view()), name="eveapi-characters-list"),
    url(r'^character/(?P<pk>\d+)/$', login_required(views.EVEAPICharacterDetailView.as_view()), name="eveapi-character"),

    url(r'^corporation/(?P<pk>\d+)/$', login_required(views.EVEAPICorporationView.as_view()), name="eveapi-corporation"),
    url(r'^corporation/(?P<corporationid>\d+)/export/$', views.eveapi_corporation_members_csv, name="eveapi-corporation-members-csv"),

    url(r'^alliance/(?P<pk>\d+)/$', login_required(views.EVEAPIAllianceView.as_view()), name="eveapi-alliance"),
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

