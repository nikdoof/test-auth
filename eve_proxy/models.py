import urllib, urllib2
import xml
import hashlib
import socket
from datetime import datetime, timedelta
from xml.dom import minidom
from django.db import models
from eve_proxy.exceptions import *
import settings

# You generally never want to change this unless you have a very good reason.

try:
    API_URL = getattr(settings, 'EVE_API_URL')
except AttributeError:
    API_URL = 'http://api.eve-online.com'

# Errors to rollback if we have a cached version of the document
# Errors 500-999 at the moment, this can be trimmed down as needed
ROLLBACK_ERRORS = range(500, 999)

class CachedDocumentManager(models.Manager):
    """
    This manager handles querying or retrieving CachedDocuments.
    """

    def construct_url(self, url_path, params):

         # Valid arguments for EVE API Calls
        allowed_params = ['userid', 'apikey', 'characterid', 'version', 'names', 'ids', 'corporationid', 'beforerefid', 'accountkey']

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
     
        if not no_cache:
            try:
                doc = super(CachedDocumentManager, self).get_query_set().get(url_path=url)
            except self.model.DoesNotExist:
                doc = None
        else:
            doc = None

        if not doc or not doc.cached_until or datetime.utcnow() > doc.cached_until:

            req = urllib2.Request(url)
            req.add_header('CCP-Contact', 'matalok@pleaseignore.com')
            try:
                conn = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                raise DocumentRetrievalError(e.code)
            except urllib2.URLError, e:
                raise DocumentRetrievalError(e.reason)

            cached_doc, created = self.get_or_create(url_path=url)
            cached_doc.body = unicode(conn.read(), 'utf-8')
            cached_doc.time_retrieved = datetime.utcnow()

            try:
                # Parse the response via minidom
                dom = minidom.parseString(cached_doc.body.encode('utf-8'))
            except xml.parsers.expat.ExpatError:
                cached_doc.cached_until = datetime.utcnow()
            else:
                cached_doc.cached_until = dom.getElementsByTagName('cachedUntil')[0].childNodes[0].nodeValue
                enode = dom.getElementsByTagName('error')
                if enode:
                   error = enode[0].getAttribute('code')
                else:
                   error = 0

            # If we have a error in the ignored error list use the cached doc, otherwise return the new doc
            if not doc or (not error or not error in ROLLBACK_ERRORS):
                cached_doc.save()
                doc = self.get(id=cached_doc.pk)

            # If this is user related, write a log instance
            if params and params.get('userid', None):
                try:
                    v = int(params.get('userid', None))
                except:
                    pass
                else:
                    ApiAccessLog(userid=v, service='Unknown', time_access=cached_doc.time_retrieved, document=url).save()

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
