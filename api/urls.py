from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication, OAuthAuthentication, NoAuthentication

from api.handlers import *

oauth = { 'authentication': OAuthAuthentication() }
noauth = { 'authentication': NoAuthentication() }

user_resource = Resource(handler=UserHandler, **oauth)
servicelogin_resource = Resource(handler=ServiceLoginHandler, **noauth)

urlpatterns = patterns('',
    url(r'^user/$', user_resource),
    url(r'^servicelogin/$', servicelogin_resource),
)

urlpatterns += patterns('piston.authentication',
    url(r'^oauth/request_token/$','oauth_request_token'),
    url(r'^oauth/authorize/$','oauth_user_auth'),
    url(r'^oauth/access_token/$','oauth_access_token'),
)

