import sys
import logging

from sentry.client.handlers import SentryHandler
from piston.resource import Resource

class SentryResource(Resource):

    def error_handler(self, e, request, meth, em_format):

        logger = logging.getLogger('piston')
        logger.addHandler(SentryHandler())

        logger.error('Piston exception: %s(%s)' % (e.__class__.__name__, e), exc_info=sys.exc_info(),
            extra={'data': {'handler': meth.im_class, 'request': request, 'get': dict(request.GET), 'post': dict(request.POST) }})

        return Resource.error_handler(self, e, request, meth, em_format)
