from django.contrib import admin
from reddit.models import RedditAccount

class RedditAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'date_created', 'link_karma', 'comment_karma')
    search_fields = ['username', 'user']

admin.site.register(RedditAccount, RedditAccountAdmin)
