import urllib, urllib2
from hashlib import sha1
from datetime import datetime, timedelta
from xml.dom import minidom
from django.db import models
from django.conf import settings
from eve_proxy.exceptions import *

# You generally never want to change this unless you have a very good reason.

try:
    API_URL = getattr(settings, 'EVE_API_URL')
except AttributeError:
    API_URL = 'https://api.eve-online.com'

# Errors to rollback if we have a cached version of the document
# Errors 500-999 at the moment, this can be trimmed down as needed
ROLLBACK_ERRORS = range(500, 999)

class CachedDocumentManager(models.Manager):
    """
    This manager handles querying or retrieving CachedDocuments.
    """

    def construct_url(self, url_path, params):

         # Valid arguments for EVE API Calls
        allowed_params = ['apikey', 'userid', 'keyid', 'vcode', 'characterid', 'version', 'names', 'ids', 'corporationid', 'beforerefid', 'accountkey']

        if len(params):
            for k, v in params.items():
                del params[k]
                if k.lower() in allowed_params:
                   params[k.lower()] = v
            url = "%s%s?%s" % (API_URL, url_path, urllib.urlencode(params))
        else:
            url = "%s%s" % (API_URL, url_path)

        return url

    def api_query(self, url_path, params={}, no_cache=False, exceptions=True):
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

        url = self.construct_url(url_path, params)
        doc_key = sha1(url).hexdigest()

        
        try:
            doc = super(CachedDocumentManager, self).get_query_set().get(pk=doc_key)
        except self.model.DoesNotExist:
            doc = CachedDocument(pk=doc_key, url_path=url)

        if not doc.cached_until or datetime.utcnow() > doc.cached_until or no_cache:

            req = urllib2.Request(url)
            req.add_header('CCP-Contact', 'matalok@pleaseignore.com')
            try:
                conn = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                print "HTTP Error Code: %s" % e.code
                raise DocumentRetrievalError(e.code)
            except urllib2.URLError, e:
                print "URLError: %s" % e.reason
                raise DocumentRetrievalError(e.reason)

            doc.body = unicode(conn.read(), 'utf-8')
            doc.time_retrieved = datetime.utcnow()

            error = 0
            try:
                # Parse the response via minidom
                dom = minidom.parseString(doc.body.encode('utf-8'))
            except:
                doc.cached_until = datetime.utcnow()
            else:
                doc.cached_until = dom.getElementsByTagName('cachedUntil')[0].childNodes[0].nodeValue
                enode = dom.getElementsByTagName('error')
                if enode:
                   error = enode[0].getAttribute('code')

            # If we have a error in the ignored error list use the cached doc, otherwise return the new doc
            if not error or not error in ROLLBACK_ERRORS:
                doc.save()
                doc = self.get(pk=doc.pk)

            # If this is user related, write a log instance
            if params and (params.get('userid', None) or params.get('keyid', None)):
                try:
                    v = int(params.get('userid', None) or int(params.get('keyid', None))) 
                except:
                    pass
                else:
                    for k in ['userid', 'apikey', 'vcode', 'keyid']:
                        if k in params: del params[k]
                    ApiAccessLog(userid=v, service='Unknown', time_access=doc.time_retrieved, document=self.construct_url(url_path, params)).save()

        return doc

class CachedDocument(models.Model):
    """
    This is a cached XML document from the EVE API.
    """
    doc_key = models.CharField(max_length=40, primary_key=True)
    url_path = models.CharField(max_length=255)
    body = models.TextField()
    time_retrieved = models.DateTimeField(blank=True, null=True)
    cached_until = models.DateTimeField(blank=True, null=True)

    # The custom manager handles the querying.
    objects = CachedDocumentManager()

    class Meta:
        verbose_name = 'Cached Document'
        verbose_name_plural = 'Cached Documents'
        ordering = ['time_retrieved']

class ApiAccessLog(models.Model):
    """
    Provides a list of API accesses made by applications or Auth
    """
    userid = models.IntegerField()
    service = models.CharField(max_length=255)
    time_access = models.DateTimeField()
    document = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'API Access Log'
        verbose_name_plural = 'API Access Logs'
        ordering = ['time_access']
