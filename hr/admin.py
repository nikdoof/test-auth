from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from hr.models import Application, Recommendation, Audit

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'character', 'status', 'recommendations')
    search_fields = ['user', 'character', 'status']

    def recommendations(self, obj):
        return len(obj.recommendation_set.all())

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

admin.site.register(Audit, AuditAdmin)

