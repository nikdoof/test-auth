from django.contrib import admin
from hr.models import Application, Recommendation, Audit, Blacklist, BlacklistSource, ApplicationConfig, TemplateMessage

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'character', 'corporation', 'status', 'application_date', 'recommendations')
    search_fields = ['id', 'user__username', 'character__name', 'status']
    list_filter = ('status',)

    def recommendations(self, obj):
        return obj.recommendation_set.all().count()

    recommendations.short_description = '# of Recommendations'

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)

admin.site.register(Application, ApplicationAdmin)

class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_character', 'application', 'recommendation_date', 'is_valid')
    search_fields = ['user_character__name']

admin.site.register(Recommendation, RecommendationAdmin)

class AuditAdmin(admin.ModelAdmin):
    list_display = ('application', 'event', 'date')
    list_filter = ('event',)

admin.site.register(Audit, AuditAdmin)

class BlacklistAdmin(admin.ModelAdmin):
    list_display = ('type', 'level', 'value', 'source', 'created_date', 'created_by')
    list_filter = ('source', 'type', 'level')
    search_fields = ('value',)

admin.site.register(Blacklist, BlacklistAdmin)

class BlacklistSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

admin.site.register(BlacklistSource, BlacklistSourceAdmin)

class ApplicationConfigAdmin(admin.ModelAdmin):
    list_display = ('corporation', 'is_accepting', 'api_required', 'api_accessmask', 'api_view')

    def get_readonly_fields(self, request, obj = None):
        if obj: #In edit mode
            return ['corporation']
        return []

admin.site.register(ApplicationConfig, ApplicationConfigAdmin)

class TemplateMessageAdmin(admin.ModelAdmin):
    list_display = ('config', 'name')

admin.site.register(TemplateMessage, TemplateMessageAdmin)
