
class IGBMiddleware(object):
    """
    Middleware to detect the EVE IGB
    """

    def process_request(self, request):

        request.is_igb = False
        request.is_igb_trusted = False

        if request.META.has_key('HTTP_EVE_TRUSTED'):
            request.is_igb = True
            if request.META.get('HTTP_EVE_TRUSTED') == 'Yes':
                request.is_igb_trusted = True
    
                            
            

