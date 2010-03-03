from django.contrib import admin
from reddit.models import RedditAccount

class RedditAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'date_created', 'link_karma', 'comment_karma', 'last_update')
    search_fields = ['username', 'user']

    fields = ('user', 'username')

    def save_model(self, request, obj, form, change):
        obj.api_update()
        obj.save()

admin.site.register(RedditAccount, RedditAccountAdmin)
