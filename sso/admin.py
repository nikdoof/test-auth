from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from sso.models import Service, ServiceAccount, SSOUser

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'api', 'active')
    search_fields = ['name', 'active']

admin.site.register(Service, ServiceAdmin)

class ServiceAccountAdmin(admin.ModelAdmin):
    list_display = ('service', 'service_uid', 'user', 'active')
    search_fields = ['service', 'service_uid', 'user', 'active']

admin.site.register(ServiceAccount, ServiceAccountAdmin)


class SSOUserProfileInline(admin.StackedInline):
    model = SSOUser
    fk_name = 'user'
    max_num = 1

# Define a new UserAdmin class
class SSOUserAdmin(UserAdmin):
    inlines = [SSOUserProfileInline, ]

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, SSOUserAdmin)
