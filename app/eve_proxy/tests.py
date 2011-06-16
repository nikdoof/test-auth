from __future__ import with_statement
import os
from datetime import datetime
import time

from django.utils import unittest
from eve_proxy.models import CachedDocument
from eve_proxy.exceptions import *

class CachedDocumentTestCase(unittest.TestCase):

    def tearDown(self):
        CachedDocument.objects.all().delete()

    def testDumbApiQuery(self):
        """ Queries the EVE API with a non authenticated request """
        url = '/server/ServerStatus.xml.aspx'

        obj = CachedDocument.objects.api_query(url, no_cache=True)

        self.assertNotEqual(obj, None, "No CachedDocument returned")
        self.assertNotEqual(obj.body, None, "CachedDocument has no body")
        self.assertNotEqual(obj.cached_until, None, "CachedDocument has no cache expiry time")
        self.assertNotEqual(obj.time_retrieved, None, "CachedDocument has no retrieval time")

    def testUserApiQuery(self):
        """ Queries the EVE API with a authenticated request """

        url = '/account/Characters.xml.aspx'

        params = {'userid': os.environ['API_USERID'] , 'apikey': os.environ['API_APIKEY']}
        obj = CachedDocument.objects.api_query(url, params=self.params, no_cache=True)

        self.assertNotEqual(obj, None, "No CachedDocument returned")
        self.assertNotEqual(obj.body, None, "CachedDocument has no body")
        self.assertNotEqual(obj.cached_until, None, "CachedDocument has no cache expiry time")
        self.assertNotEqual(obj.time_retrieved, None, "CachedDocument has no retrieval time")        

    def testCaching(self):
        """ Tests if objects are being cached correctly """

        url = '/server/ServerStatus.xml.aspx'
	obj = CachedDocument.objects.api_query(url, no_cache=True)
	obj2 = CachedDocument.objects.api_query(url)

        self.assertEqual(obj.pk, obj2.pk, "Objects are not caching correctly")

    def testCacheExpiry(self):
        """ Tests that cache expiry is working """

        url = '/server/ServerStatus.xml.aspx'
        obj = CachedDocument.objects.api_query(url, no_cache=True)
        ret_time = obj.time_retrieved
        obj.cached_until = datetime.utcnow()
        obj.save()

        time.sleep(1)

        obj2 = CachedDocument.objects.api_query(url)
        
        self.assertEqual(obj.pk, obj2.pk, "Cache Expiry test returned different objects")
        self.assertNotEqual(obj2.time_retrieved, ret_time, "Retrieval time not updated")

    def testInvalidApiQuery(self):
        """ Attempts to request a invalid EVE API endpoint """

        url = '/server/ServerStatus.xml.aspx'
        
        with self.assertRaises(DocumentRetrievalError):
            obj = CachedDocument.objects.api_query(url, no_cache=True)

