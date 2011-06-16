from django.contrib import admin
from eve_proxy.models import CachedDocument, ApiAccessLog

class CachedDocumentAdmin(admin.ModelAdmin):
    model = CachedDocument
    list_display = ('doc_key', 'url_path', 'time_retrieved', 'cached_until')
    readonly_fields = ('doc_key', 'url_path', 'body', 'time_retrieved', 'cached_until')
    verbose_name = 'Cached Document'
    verbose_name_plural = 'Cached Documents'

    def has_add_permission(self, request):
        return False

admin.site.register(CachedDocument, CachedDocumentAdmin)

class ApiAccessLogAdmin(admin.ModelAdmin):
    model = ApiAccessLog
    list_display = ('userid', 'service', 'document', 'time_access')
    list_filter = ('service',)
    verbose_name = 'API Access Log'
    verbose_name_plural = 'API Access Logs'

    def has_add_permission(self, request):
        return False

admin.site.register(ApiAccessLog, ApiAccessLogAdmin)
