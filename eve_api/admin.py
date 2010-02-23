"""
Admin interface models. Automatically detected by admin.autodiscover().
"""
from django.contrib import admin
from eve_api.models import *

class EVEAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = ['id']
admin.site.register(EVEAccount, EVEAccountAdmin)

class EVEPlayerCharacterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'corporation')
    search_fields = ['id', 'name']
admin.site.register(EVEPlayerCharacter, EVEPlayerCharacterAdmin)

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
