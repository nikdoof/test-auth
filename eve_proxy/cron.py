import logging
from datetime import datetime

from eve_proxy.models import CachedDocument

class ClearStaleCache():
        """
        Clears out any stale cache entries
        """

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger
                
        def job(self, args):
            objs = CachedDocument.objects.filter(cached_until__lt=datetime.utcnow())
            self._logger.info('Removing %s stale cache documents' % objs.count())
            objs.delete()

class FlushCache():
        """
        Flushes the entire cache
        """

        @property
        def _logger(self):
            if not hasattr(self, '__logger'):
                self.__logger = logging.getLogger(__name__)
            return self.__logger
                
        def job(self, args):
            objs = CachedDocument.objects.all()
            self._logger.info('Removing %s stale cache documents' % objs.count())
            objs.delete()

