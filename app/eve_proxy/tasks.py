import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.utils.timezone import now

from celery.task import task

from eve_proxy.models import CachedDocument, ApiAccessLog


@task(ignore_result=True)
def clear_stale_cache(cache_extension=0):
    log = clear_stale_cache.get_logger()

    time = now() - timedelta(seconds=cache_extension)
    objs = CachedDocument.objects.filter(cached_until__lt=time)
    log.info('Removing %s stale cache documents' % objs.count())
    objs.delete()


@task(ignore_result=True)
def clear_old_logs():
    log = clear_old_logs.get_logger()

    time = now() - timedelta(days=getattr(settings, 'EVE_PROXY_KEEP_LOGS', 30))
    objs = ApiAccessLog.objects.filter(time_access__lt=time)
    log.info('Removing %s old access logs' % objs.count())
    objs.delete()
