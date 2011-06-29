from django.conf.urls.defaults import *
from piston.authentication import NoAuthentication, OAuthAuthentication

from api.resource import SentryResource as Resource
from api.auth import APIKeyAuthentication
from api.handlers import *

noauth = {'authentication': NoAuthentication() }
apikeyauth = {'authentication': APIKeyAuthentication() }
oauth = {'authentication': OAuthAuthentication() }

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

# OAuth
urlpatterns += patterns('piston.authentication',
    url(r'^oauth/request_token/$','oauth_request_token'),
    url(r'^oauth/authorize/$','oauth_user_auth'),
    url(r'^oauth/access_token/$','oauth_access_token'), 
)

urlpatterns += patterns('api.views',
    url(r'^oauth/tokens/$', 'oauth_list_tokens', name='oauth-list-tokens'),
    url(r'^oauth/tokens/(?P<key>.*)$', 'oauth_revoke_token', name='oauth-revoke-token'),
)

oauth_optimer_resource = Resource(handler=OAuthOpTimerHandler, **oauth)
oauth_eveapi_resource = Resource(handler=OAuthOpTimerHandler, **oauth)
oauth_chars_resource = Resource(handler=OAuthCharacterHandler, **oauth)

# API
urlpatterns += patterns('',
    url(r'^oauth/optimer/$', oauth_optimer_resource),
    url(r'^oauth/eveapi/$', oauth_eveapi_resource),
    url(r'^oauth/character/$', oauth_chars_resource),

)

