from django.contrib import admin
from reddit.models import RedditAccount


class RedditAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'date_created', 'link_karma', 'comment_karma', 'last_update', 'validated', 'is_valid')
    search_fields = ['username']

    fields = ('user', 'username', 'validated')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.api_update()
        obj.save()

admin.site.register(RedditAccount, RedditAccountAdmin)
