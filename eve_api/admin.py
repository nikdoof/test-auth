"""
Admin interface models. Automatically detected by admin.autodiscover().
"""
from django.contrib import admin
from eve_api.models import *

from eve_api.tasks import import_apikey

def account_api_update(modeladmin, request, queryset):
    for obj in queryset:
        import_apikey.delay(api_key=obj.api_key, api_userid=obj.api_user_id)

account_api_update.short_description = "Update account from the EVE API"

class EVEAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'api_keytype', 'api_status', 'api_last_updated')
    search_fields = ['id', 'user__username']
    readonly_fields = ('api_keytype', 'api_user_id', 'api_key', 'api_status', 'characters', 'api_last_updated')
    filter_horizontal = ('characters',)

    actions = [account_api_update]

admin.site.register(EVEAccount, EVEAccountAdmin)

class EVEPlayerCharacterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'corporation')
    search_fields = ['id', 'name']
admin.site.register(EVEPlayerCharacter, EVEPlayerCharacterAdmin)

class EVEPlayerCharacterRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'roleid', 'name')
    search_fields = ['roleid', 'name']
admin.site.register(EVEPlayerCharacterRole, EVEPlayerCharacterRoleAdmin)

class EVEPlayerCorporationInline(admin.TabularInline):
    model = EVEPlayerCorporation
    fields = ('name', 'ticker')
    extra = 0

class EVEPlayerAllianceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ticker', 'member_count', 'date_founded')
    search_fields = ['name', 'ticker']
    date_hierarchy = 'date_founded'
    inlines = [EVEPlayerCorporationInline]
admin.site.register(EVEPlayerAlliance, EVEPlayerAllianceAdmin)

class EVEPlayerCorporationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ticker', 'member_count', 'alliance')
    search_fields = ['name', 'ticker']
admin.site.register(EVEPlayerCorporation, EVEPlayerCorporationAdmin)

class EVESkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'group' )
    search_fields = ['id', 'name']
admin.site.register(EVESkill, EVESkillAdmin)

class EVESkillGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
    search_fields = ['id', 'name']
admin.site.register(EVESkillGroup, EVESkillGroupAdmin)

