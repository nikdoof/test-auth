from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from api.handlers import *

auth = HttpBasicAuthentication(realm="My Realm")
#ad = { 'authentication': auth }
ad = {}

user_resource = Resource(handler=UserHandler, **ad)
serviceaccount_resource = Resource(handler=ServiceAccountHandler, **ad)
login_resource = Resource(handler=LoginHandler, **ad)

urlpatterns = patterns('',
    url(r'^login/$', login_resource),
    url(r'^user/$', user_resource),
    url(r'^user/(?P<id>\d+)/$', user_resource),
    url(r'^serviceaccount/$', serviceaccount_resource),
    url(r'^serviceaccount/(?P<id>\d+)/$', serviceaccount_resource),
)
