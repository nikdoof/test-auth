from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from hr.models import Application, Recommendation

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'character', 'status')
    search_fields = ['user', 'character', 'status']

admin.site.register(Application, ApplicationAdmin)

class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_character')
    search_fields = ['user_character']

admin.site.register(Recommendation, RecommendationAdmin)

