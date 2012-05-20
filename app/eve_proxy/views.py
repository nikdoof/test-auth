from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from eve_proxy.models import CachedDocument


class EVEAPIProxyView(View):
    """Allows for standard EVE API calls to be proxied through your application"""

    def get(self, request, *args, **kwargs):
        return self.get_document(request, request.GET)
    
    def post(self, request, *args, **kwargs):
        return self.get_document(request, request.POST)
    
    def get_document(self, request, params):
        url_path = request.META['PATH_INFO'].replace(reverse('eveproxy-apiproxy'),"/")

        if url_path == '/' or url_path == '':
            # If they don't provide any kind of query, shoot a quick error message.
            return HttpResponseNotFound('No API query specified.')
        
        if 'userID' in params and not 'service' in params:
            return HttpResponse('No Service ID provided.')

        try:
            cached_doc = CachedDocument.objects.api_query(url_path, params, exceptions=False)
        except:
            return HttpResponseServerError('Error occured')

        if cached_doc:
            return HttpResponse(cached_doc.body, mimetype='text/xml')

        return HttpResponseNotFound('Error retrieving the document')
