from django.contrib import admin
from reddit.models import RedditAccount
from reddit.forms import RedditAccountForm

from datetime import date

class RedditAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'date_created', 'link_karma', 'comment_karma', 'last_update', 'validated', 'is_valid')
    search_fields = ['username']

    fields = ('user', 'username', 'validated')

    #form = RedditAccountForm

    def is_valid(self, obj):
        if not obj.date_created:
            return False

        # Account 3 months old?
        if (date.today() - obj.date_created.date()).days >= 90:
            return True

        # Account created after 9/2/10 and before 13/2/10
        if obj.date_created.date() >= date(2010, 2, 9) and obj.date_created.date() <= date(2010, 2, 13):
            return True
    
        return False


    is_valid.short_description = 'Dreddit Eligible'
    is_valid.boolean = True


    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.api_update()
        obj.save()

admin.site.register(RedditAccount, RedditAccountAdmin)
