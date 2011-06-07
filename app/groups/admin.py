from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from groups.models import GroupInformation, GroupRequest

class GroupRequestAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'status', 'created_date', 'changed_by', 'changed_date')
    search_fields = ('user__username', 'group__name')
    list_filter = ('status',)

admin.site.register(GroupRequest, GroupRequestAdmin)

class SSOGroupInformationInline(admin.StackedInline):
    model = GroupInformation
    fk_name = 'group'
    max_num = 1

    readonly_fields = ('admins',)

# Define a new UserAdmin class
class SSOGroupAdmin(GroupAdmin):
    inlines = [SSOGroupInformationInline, ]

# Re-register UserAdmin
admin.site.unregister(Group)
admin.site.register(Group, SSOGroupAdmin)


