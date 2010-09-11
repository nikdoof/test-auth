"""
Admin interface models. Automatically detected by admin.autodiscover().
"""
from django.contrib import admin
from eve_api.models import *

from eve_api.api_puller.accounts import import_eve_account

def account_api_update(modeladmin, request, queryset):
    for obj in queryset:
        import_eve_account(obj.api_key, obj.api_user_id)

account_api_update.short_description = "Update account from the EVE API"

class EVEAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'api_keytype', 'api_status', 'api_last_updated')
    search_fields = ['id']

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
