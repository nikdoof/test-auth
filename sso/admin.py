"""
Admin interface models. Automatically detected by admin.autodiscover().
"""
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from sso.models import Service, ServiceAccount, SSOUser

admin.site.register(Service)
admin.site.register(ServiceAccount)

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
