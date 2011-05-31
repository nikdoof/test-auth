from django.contrib import admin
from api.models import AuthAPIKey, AuthAPILog


class AuthAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'url', 'active')
    search_fields = ['name']
    list_filter = ('active',)


class AuthAPILogAdmin(admin.ModelAdmin):
    list_display = ('key', 'url', 'access_datetime')
    list_filter = ('key',)

admin.site.register(AuthAPIKey, AuthAPIKeyAdmin)
admin.site.register(AuthAPILog, AuthAPILogAdmin)
