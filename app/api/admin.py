from django.contrib import admin
from api.models import AuthAPIKey, AuthAPILog
from piston.models import Consumer, Token

class AuthAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'url', 'active')
    search_fields = ['name']
    list_filter = ('active',)


class AuthAPILogAdmin(admin.ModelAdmin):
    list_display = ('key', 'url', 'access_datetime')
    list_filter = ('key',)

    def has_add_permission(self, request):
        return False


admin.site.register(AuthAPIKey, AuthAPIKeyAdmin)
admin.site.register(AuthAPILog, AuthAPILogAdmin)
admin.site.register(Consumer, admin.ModelAdmin)
admin.site.register(Token, admin.ModelAdmin)
