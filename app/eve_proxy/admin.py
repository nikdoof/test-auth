from django.contrib import admin
from eve_proxy.models import CachedDocument, ApiAccessLog

class CachedDocumentAdmin(admin.ModelAdmin):
    model = CachedDocument
    list_display = ('url_path', 'time_retrieved', 'cached_until')
    verbose_name = 'Cached Document'
    verbose_name_plural = 'Cached Documents'
admin.site.register(CachedDocument, CachedDocumentAdmin)

class ApiAccessLogAdmin(admin.ModelAdmin):
    model = ApiAccessLog
    list_display = ('userid', 'service', 'document', 'time_access')
    verbose_name = 'API Access Log'
    verbose_name_plural = 'API Access Logs'
admin.site.register(ApiAccessLog, ApiAccessLogAdmin)
