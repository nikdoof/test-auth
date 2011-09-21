import sys
import logging

from piston.resource import Resource

class SentryResource(Resource):

    def error_handler(self, e, request, meth, em_format):

        logger = logging.getLogger('piston')

        logger.error('Piston exception: %s(%s)' % (e.__class__.__name__, e), exc_info=sys.exc_info(),
            extra={'data': {'handler': meth.im_class, 'request': request, 'get': dict(request.GET), 'post': dict(request.POST) }})

        return super(SentryResource, self).error_handler(e, request, meth, em_format)
