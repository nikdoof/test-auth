from django.contrib import admin
from api.models import AuthAPIKey, AuthAPILog

class AuthAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'url', 'active')
    search_fields = ['name']

admin.site.register(AuthAPIKey, AuthAPIKeyAdmin)

class AuthAPILogAdmin(admin.ModelAdmin):
    list_display = ('key', 'url', 'access_datetime')

admin.site.register(AuthAPILog, AuthAPILogAdmin)
