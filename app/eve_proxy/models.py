import sys
import logging
import urllib, urllib2
from hashlib import sha1
from datetime import datetime, timedelta
from xml.dom import minidom
from django.db import models, IntegrityError
from django.conf import settings
from eve_proxy.exceptions import *

# API URL, can be overriden in the configuration
API_URL = getattr(settings, 'EVE_API_URL', 'https://api.eve-online.com')

# Errors to rollback if we have a cached version of the document
ROLLBACK_ERRORS = range(516, 902)

# Errors ignored if encountered, as they're valid responses in some cases
IGNORED_ERRORS = range(200, 223)

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

    def api_query(self, url_path, params={}, no_cache=False, exceptions=True, timeout=getattr(settings, 'EVE_PROXY_TIMEOUT', 60), service="Auth"):
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

        logger = logging.getLogger('eve_proxy.CachedDocument')

        url = self.construct_url(url_path, params)
        doc_key = sha1(url).hexdigest()

        logger.debug('Requesting URL: %s' % url)

        try:
            doc = super(CachedDocumentManager, self).get_query_set().get(pk=doc_key)
            created = False
        except self.model.DoesNotExist:
            doc = CachedDocument(pk=doc_key, url_path=url)
            created = True

        if created or not doc.cached_until or datetime.utcnow() > doc.cached_until or no_cache:

            req = urllib2.Request(url)
            # Add a header with the admin information in, so CCP can traceback the requests if needed
            if settings.ADMINS:
                req.add_header('CCP-Contact', str(', ').join(['%s <%s>' % (name, email) for name, email in settings.ADMINS]))

            try:
                if sys.version_info < (2, 6):
                    conn = urllib2.urlopen(req)
                else:
                    conn = urllib2.urlopen(req, timeout=timeout)
            except urllib2.HTTPError, e:
                if not created:
                    pass
                logger.error('HTTP Error Code: %s' % e.code, exc_info=sys.exc_info(), extra={'data': {'api-url': url}})
                raise DocumentRetrievalError(e.code)
            except urllib2.URLError, e:
                if not created:
                    pass
                logger.error('URL Error: %s' % e, exc_info=sys.exc_info(), extra={'data': {'api-url': url}})
                raise DocumentRetrievalError(e.reason)
            else:
                doc.body = unicode(conn.read(), 'utf-8')
                doc.time_retrieved = datetime.utcnow()

            error = 0
            try:
                # Parse the response via minidom
                dom = minidom.parseString(doc.body.encode('utf-8'))
            except:
                doc.cached_until = datetime.utcnow()
            else:
                date = datetime.strptime(dom.getElementsByTagName('cachedUntil')[0].childNodes[0].nodeValue, '%Y-%m-%d %H:%M:%S')
                # Add 30 seconds to the cache timers, avoid hitting too early and account for some minor clock skew.
                doc.cached_until = date + timedelta(seconds=getattr(settings, 'EVE_PROXY_CACHE_ADJUSTMENT', 30))
                enode = dom.getElementsByTagName('error')
                if enode:
                   error = enode[0].getAttribute('code')

            if error:
                # If we have a rollback error, try and retreive a correct version from the DB
                if int(error) in ROLLBACK_ERRORS:
                    try:
                        doc = self.get(pk=doc.pk)
                    except self.DoesNotExist:
                        doc.save()
                else:
                    if not int(error) in IGNORED_ERRORS:
                        logger.error("API Error %s encountered - %s" % (error, url), extra={'data': {'api-url': url, 'error': error, 'document': doc.body}})
                    else:
                        doc.save()
            else:
                doc.save()

            # If this is user related, write a log instance
            if params and (params.get('userid', None) or params.get('keyid', None)):
                try:
                    v = int(params.get('userid', None) or int(params.get('keyid', None))) 
                except:
                    pass
                else:
                    fparams = {}
                    for k in params:
                        if not k in ['userid', 'apikey', 'vcode', 'keyid']: fparams[k] = params[k]

                    ApiAccessLog(userid=v, service=service, time_access=doc.time_retrieved, document=self.construct_url(url_path, fparams)).save()

        return doc

class CachedDocument(models.Model):
    """
    This is a cached XML document from the EVE API.
    """
    doc_key = models.CharField("Document Key", max_length=40, primary_key=True, help_text="A unique SHA1 hash of the request")
    url_path = models.CharField("URL Path", max_length=255, help_text="The full EVE API url path of this document")
    body = models.TextField("Body", help_text="The raw XML document from the EVE API")
    time_retrieved = models.DateTimeField(blank=True, null=True, help_text="UTC date/time of when the document was retreived from the EVE API")
    cached_until = models.DateTimeField(blank=True, null=True, help_text="UTC date/time specifying when this document should be cached until")

    # The custom manager handles the querying.
    objects = CachedDocumentManager()

    def __unicode__(self):
        return u'%s - %s' % (self.doc_key, self.time_retrieved)

    class Meta:
        verbose_name = 'Cached Document'
        verbose_name_plural = 'Cached Documents'
        ordering = ['-time_retrieved']


class ApiAccessLog(models.Model):
    """
    Provides a list of API accesses made by applications or Auth
    """
    userid = models.IntegerField("User ID", help_text="The API User ID related to this log")
    service = models.CharField("Service Name", max_length=255, help_text="The service name that requested the document")
    time_access = models.DateTimeField("Date/Time Accessed", help_text="The date/time the document was requested")
    document = models.CharField("Document Path", max_length=255, help_text="The path to the requested document")

    def __unicode__(self):
        return u'Key %s - %s' % (self.userid, self.document)

    class Meta:
        verbose_name = 'API Access Log'
        verbose_name_plural = 'API Access Logs'
        ordering = ['-time_access']
