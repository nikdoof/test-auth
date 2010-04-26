from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication, OAuthAuthentication

from api.handlers import *

auth = OAuthAuthentication()
#auth = HttpBasicAuthentication(realm="Auth API")
ad = { 'authentication': auth }
#ad = {}

user_resource = Resource(handler=UserHandler, **ad)
login_resource = Resource(handler=LoginHandler, **ad)
logout_resource = Resource(handler=LogoutHandler, **ad)
access_resource = Resource(handler=AccessHandler, **ad)

urlpatterns = patterns('',
    url(r'^login/$', login_resource),
    url(r'^logout/$', logout_resource),
    url(r'^access/$', access_resource),
    url(r'^user/$', user_resource),
#    url(r'^user/(?P<id>\d+)/$', user_resource),
#    url(r'^serviceaccount/$', serviceaccount_resource),
#    url(r'^serviceaccount/(?P<id>\d+)/$', serviceaccount_resource),
)

urlpatterns += patterns('piston.authentication',
    url(r'^oauth/request_token/$','oauth_request_token'),
    url(r'^oauth/authorize/$','oauth_user_auth'),
    url(r'^oauth/access_token/$','oauth_access_token'),
)

