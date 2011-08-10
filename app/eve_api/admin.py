"""
Admin interface models. Automatically detected by admin.autodiscover().
"""
from django.contrib import admin
import celery
from eve_api.models import *
from eve_api.tasks import import_apikey, import_eve_character

def account_api_update(modeladmin, request, queryset):
    for obj in queryset:
        import_apikey.delay(api_key=obj.api_key, api_userid=obj.api_user_id)

account_api_update.short_description = "Update account from the EVE API"

def char_api_update(modeladmin, request, queryset):
    for obj in queryset:
        if obj.eveaccount_set.count():
            import_eve_character.delay(obj.id, obj.eveaccount_set.all()[0].api_key, obj.eveaccount_set.all()[0].api_user_id)
        else:
            import_eve_character.delay(obj.id)

char_api_update.short_description = "Update character information from the EVE API"

class EVEAccountAdmin(admin.ModelAdmin):
    list_display = ('api_user_id', 'user', 'api_keytype', 'api_status', 'api_last_updated')
    search_fields = ['api_user_id', 'user__username']
    readonly_fields = ('api_keytype', 'api_status', 'characters', 'api_last_updated', 'characters')
    actions = [account_api_update]

    def save_model(self, request, obj, form, change):
        admin.ModelAdmin.save_model(self, request, obj, form, change)
        task = import_apikey.delay(api_key=obj.api_key, api_userid=obj.api_user_id)
        try:
            task.wait(10)
        except celery.exceptions.TimeoutError:
            self.message_user(request, "API Key %s has been queued for an update." % obj.api_user_id)
        except:
            self.message_user(request, "An error was encountered why updating the API Key")

admin.site.register(EVEAccount, EVEAccountAdmin)

class EVEPlayerCharacterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'corporation')
    search_fields = ['id', 'name']
    actions = [char_api_update]

    def has_add_permission(self, request):
        return False

admin.site.register(EVEPlayerCharacter, EVEPlayerCharacterAdmin)

class EVEPlayerCharacterRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'roleid', 'name')
    search_fields = ['roleid', 'name']

    def has_add_permission(self, request):
        return False

admin.site.register(EVEPlayerCharacterRole, EVEPlayerCharacterRoleAdmin)

class EVEPlayerCorporationInline(admin.TabularInline):
    model = EVEPlayerCorporation
    fields = ('name', 'ticker')
    extra = 0

    def has_add_permission(self, request):
        return False


class EVEPlayerAllianceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ticker', 'member_count', 'date_founded')
    search_fields = ['name', 'ticker']
    date_hierarchy = 'date_founded'
    inlines = [EVEPlayerCorporationInline]

    def has_add_permission(self, request):
        return False

admin.site.register(EVEPlayerAlliance, EVEPlayerAllianceAdmin)

class EVEPlayerCorporationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ticker', 'member_count', 'alliance')
    search_fields = ['name', 'ticker']

    def has_add_permission(self, request):
        return False

admin.site.register(EVEPlayerCorporation, EVEPlayerCorporationAdmin)

class EVESkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'group' )
    search_fields = ['id', 'name']

    def has_add_permission(self, request):
        return False

admin.site.register(EVESkill, EVESkillAdmin)

class EVESkillGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
    search_fields = ['id', 'name']

    def has_add_permission(self, request):
        return False

admin.site.register(EVESkillGroup, EVESkillGroupAdmin)

