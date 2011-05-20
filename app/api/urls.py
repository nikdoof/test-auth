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
announce_resource = Resource(handler=AnnounceHandler, **apikeyauth)

urlpatterns = patterns('',
    url(r'^user/$', user_resource),
    url(r'^login/$', login_resource),
    url(r'^eveapi/$', eveapi_resource),
    url(r'^eveapi/', eveapiproxy_resource, name='api-eveapiproxy'),
    url(r'^character/$', characters_resource),
    url(r'^optimer/$', optimer_resource),
    url(r'^blacklist/$', blacklist_resource),
    url(r'^announce/$', announce_resource),
)

urlpatterns += patterns('',
    url(r'^1.0/user/$', user_resource),
    url(r'^1.0/login/$', login_resource),
    url(r'^1.0/eveapi/$', eveapi_resource),
    url(r'^1.0/eveapi/', eveapiproxy_resource, name='api-eveapiproxy'),
    url(r'^1.0/character/$', characters_resource),
    url(r'^1.0/optimer/$', optimer_resource),
    url(r'^1.0/blacklist/$', blacklist_resource),
    url(r'^1.0/announce/$', announce_resource),
)

# v2 APIs
v2_authenticate_resource = Resource(handler=V2AuthenticationHandler, **noauth)
v2_eveapiproxy_resource = Resource(handler=V2EveAPIProxyHandler, **apikeyauth)
v2_user_resource = Resource(handler=V2UserHandler, **apikeyauth)

urlpatterns += patterns('',
    url(r'^2.0/authenticate/$', v2_authenticate_resource, name='v2-api-authenticate'),
    url(r'^2.0/proxy/', v2_eveapiproxy_resource, name='v2-api-eveapiproxy'),
    url(r'^2.0/user/(?P<userid>\d+)/$', v2_user_resource, name='v2-api-user'),
)
