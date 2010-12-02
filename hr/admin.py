from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from hr.models import Application, Recommendation, Audit, Blacklist, BlacklistSource

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'character', 'corporation', 'status', 'recommendations')
    search_fields = ['user', 'character', 'status']
    list_filter = ('status',)

    def recommendations(self, obj):
        return obj.recommendation_set.all().count()

    recommendations.short_description = '# of Recommendations'

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)

admin.site.register(Application, ApplicationAdmin)

class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_character', 'application')
    search_fields = ['user_character']

admin.site.register(Recommendation, RecommendationAdmin)

class AuditAdmin(admin.ModelAdmin):
    list_display = ('application', 'event', 'date')
    list_filter = ('event',)

admin.site.register(Audit, AuditAdmin)

class BlacklistAdmin(admin.ModelAdmin):
    list_display = ('type', 'value', 'source', 'created_date', 'created_by')
    list_filter = ('source', 'type')
    search_fields = ('value',)

admin.site.register(Blacklist, BlacklistAdmin)

class BlacklistSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

admin.site.register(BlacklistSource, BlacklistSourceAdmin)
