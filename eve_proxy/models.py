import httplib
import urllib
import xml
import hashlib
from datetime import datetime, timedelta
from xml.dom import minidom
from django.db import models
from eve_api.api_exceptions import APIAuthException, APINoUserIDException

# You generally never want to change this unless you have a very good reason.
API_URL = 'api.eve-online.com'

class CachedDocumentManager(models.Manager):
    """
    This manager handles querying or retrieving CachedDocuments.
    """

    def get_document_id(self, url_path, params):
        if params:
            if 'service' in params:
                del params['service']
            paramstr = urllib.urlencode(params)
        else:
            paramstr = ''

        return hashlib.sha1('%s?%s' % (url_path, paramstr)).hexdigest()

    def cache_from_eve_api(self, url_path, params):
        """
        Connect to the EVE API server, send the request, and cache it to
        a CachedDocument. This is typically not something you want to call
        directly. Use api_query().
        """

        method = 'GET'
        paramstr = ''

        if params:
            if 'service' in params:
                service = params['service']
                del params['service']
            else:
                service = 'auth'
            paramstr = urllib.urlencode(params)

        if len(paramstr.strip()) > 0:
            method = 'POST'

        headers = {"Content-type": "application/x-www-form-urlencoded"}
        conn = httplib.HTTPConnection(API_URL)
        conn.request(method, url_path, paramstr, headers)
        response = conn.getresponse()
        
        print service, url_path, paramstr, response.status

        if response.status == 200:
            doc_id = self.get_document_id(url_path, params)
            cached_doc, created = self.get_or_create(url_path=doc_id)
            cached_doc.body = unicode(response.read(), 'utf-8')
            cached_doc.time_retrieved = datetime.utcnow()

            try:
                # Parse the response via minidom
                dom = minidom.parseString(cached_doc.body.encode('utf-8'))
            except xml.parsers.expat.ExpatError:
                cached_doc.cached_until = datetime.utcnow()
            else:
                cached_doc.cached_until = dom.getElementsByTagName('cachedUntil')[0].childNodes[0].nodeValue           

            # If this is user related, write a log instance
            if params and 'userID' in params and type(params['userID']) == long:
                log = ApiAccessLog()
                log.userid = params['userID']
                log.service = service
                log.time_access = cached_doc.time_retrieved
                log.document = url_path
                log.save()

            # Finish up and return the resulting document just in case.
            cached_doc.save()
            cached_doc = self.get(id=cached_doc.pk)

            return cached_doc
    
    def api_query(self, url_path, params=None, no_cache=False, exceptions=True):
        """
        Transparently handles querying EVE API or retrieving the document from
        the cache.
        
        Arguments:
        url_path: (string) Path to the EVE API page to query. For example:
                           /eve/ErrorList.xml.aspx
        params: (dictionary/string) A dictionary of extra parameters to include.
                                    May also be a string representation of
                                    the query: userID=1&characterID=xxxxxxxx
        """

        doc_id = self.get_document_id(url_path, params)
     
        doc = None
        if not no_cache:
            try:
                doc = super(CachedDocumentManager, self).get_query_set().get(url_path=doc_id)
            except self.model.DoesNotExist:
                pass
    
        # EVE uses UTC.
        current_eve_time = datetime.utcnow()

        if not doc or current_eve_time > doc.cached_until:
            doc = self.cache_from_eve_api(url_path, params)

        if doc:
            dom = minidom.parseString(doc.body.encode('utf-8'))
            
            if dom:
                error_node = dom.getElementsByTagName('error')
                if error_node and exceptions:
                    error_code = error_node[0].getAttribute('code')
                    # User specified an invalid userid and/or auth key.
                    if error_code == '203':
                        raise APIAuthException()
                    elif error_code == '106':
                        raise APINoUserIDException()

            return doc

class CachedDocument(models.Model):
    """
    This is a cached XML document from the EVE API.
    """
    url_path = models.CharField(max_length=255)
    body = models.TextField()
    time_retrieved = models.DateTimeField(blank=True, null=True)
    cached_until = models.DateTimeField(blank=True, null=True)

    # The custom manager handles the querying.
    objects = CachedDocumentManager()

class ApiAccessLog(models.Model):
    """
    Provides a list of API accesses made by applications or Auth
    """
    userid = models.IntegerField()
    service = models.CharField(max_length=255)
    time_access = models.DateTimeField()
    document = models.CharField(max_length=255)
