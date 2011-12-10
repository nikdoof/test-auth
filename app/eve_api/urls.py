from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from eve_api import views

urlpatterns = patterns('',
    url(r'^eveapi/add/$', views.eveapi_add, name="eveapi-add"),
    url(r'^eveapi/update/(?P<userid>\d+)/$', views.eveapi_update, name="eveapi-update"),
    url(r'^eveapi/delete/(?P<userid>\d+)/$', views.eveapi_del, name="eveapi-delete"),
    url(r'^eveapi/refresh/(?P<userid>\d+)/$', views.eveapi_refresh, name="eveapi-refresh"),
    url(r'^eveapi/log/(?P<userid>\d+)/$', views.eveapi_log, name="eveapi-log"),
    url(r'^eveapi/access/(?P<slug>\d+)/$', login_required(views.EVEAPIAccessView.as_view()), name="eveapi-accessview"),

    url(r'^character/list/$', views.eveapi_character, name="eveapi-characters-list"),
    url(r'^character/(?P<charid>\d+)/$', views.eveapi_character, name="eveapi-character"),

    url(r'^corporation/(?P<corporationid>\d+)/$', views.eveapi_corporation, name="eveapi-corporation"),
    url(r'^corporation/(?P<corporationid>\d+)/export/$', views.eveapi_corporation_members_csv, name="eveapi-corporation-members-csv"),

    url(r'^alliance/(?P<allianceid>\d+)/$', views.eveapi_alliance, name="eveapi-alliance"),
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

