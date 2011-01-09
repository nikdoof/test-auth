from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import NoAuthentication

from api.auth import APIKeyAuthentication
from api.handlers import *

noauth = {'authentication': NoAuthentication() }
apikeyauth = {'authentication': APIKeyAuthentication() }

# v1 APIs
user_resource = Resource(handler=UserHandler, **apikeyauth)
login_resource = Resource(handler=LoginHandler, **noauth)
eveapi_resource = Resource(handler=EveAPIHandler, **apikeyauth)
eveapiproxy_resource = Resource(handler=EveAPIProxyHandler, **apikeyauth)
optimer_resource = Resource(handler=OpTimerHandler, **apikeyauth)
blacklist_resource = Resource(handler=BlacklistHandler, **apikeyauth)
characters_resource = Resource(handler=CharacterHandler, **apikeyauth)

urlpatterns = patterns('',
    url(r'^user/$', user_resource),
    url(r'^login/$', login_resource),
    url(r'^eveapi/$', eveapi_resource),
    url(r'^eveapi/', eveapiproxy_resource, name='api-eveapiproxy'),
    url(r'^character/$', characters_resource),
    url(r'^optimer/$', optimer_resource),
    url(r'^blacklist/$', blacklist_resource),
)

# v2 APIs
v2_authenticate_resource = Resource(handler=AuthenticationHandler, **noauth)

urlpatterns += patterns('',
    url(r'^v2/authenticate/$', v2_authenticate_resource),
)
