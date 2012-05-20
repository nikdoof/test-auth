from django.conf.urls.defaults import *

from eve_proxy.views import EVEAPIProxyView

urlpatterns = patterns('eve_proxy.views',
    # This view can be used just like EVE API's http://api.eve-online.com.
    # Any parameters or URL paths are sent through the cache system and
    # forwarded to the EVE API site as needed.
    url(r'^', EVEAPIProxyView.as_view(), name='eveproxy-apiproxy'),
)
