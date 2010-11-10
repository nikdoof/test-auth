import logging
from datetime import datetime, timedelta
from celery.decorators import task
from eve_proxy.models import CachedDocument

@task(ignore_result=True)
def clear_stale_cache(cache_extension=0):
    log = clear_stale_cache.get_logger()

    time = datetime.utcnow() - timedelta(seconds=cache_extension)
    objs = CachedDocument.objects.filter(cached_until__lt=datetime.utcnow()).delete()
    self.log.info('Removed %s stale cache documents' % objs.count())
