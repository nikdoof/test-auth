from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes import generic

from sso.models import Service, ServiceAccount, SSOUser, SSOUserNote, PermissionRule, PermissionRuleset


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'api', 'active')
    search_fields = ['name']
    list_filter = ('active',)


class ServiceAccountAdmin(admin.ModelAdmin):
    list_display = ('service', 'service_uid', 'user', 'active')
    search_fields = ['service_uid', 'user__username']
    list_filter = ('service', 'active')


class SSOUserProfileInline(admin.StackedInline):
    model = SSOUser
    fk_name = 'user'
    max_num = 1
    readonly_fields = ('primary_character',)
    can_delete = False


# Define a new UserAdmin class
class SSOUserAdmin(UserAdmin):
    inlines = [SSOUserProfileInline, ]


class SSOUserNoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'note', 'date_created', 'created_by')
    search_fields = ['user__username']


class PermissionRuleInline(generic.GenericTabularInline):
    model = PermissionRule
    extra = 1
    ct_field = ''
    ct_fk_field = ''


class PermissionRuleAdmin(admin.ModelAdmin):
    pass


class PermissionRulesetAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'group__name')
    inlines = [PermissionRuleInline,]




admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceAccount, ServiceAccountAdmin)
admin.site.unregister(User)
admin.site.register(User, SSOUserAdmin)
admin.site.register(SSOUserNote, SSOUserNoteAdmin)
admin.site.register(PermissionRuleset, PermissionRulesetAdmin)
admin.site.register(PermissionRule, PermissionRuleAdmin)
