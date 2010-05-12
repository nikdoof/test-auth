from django.db import models
from django.contrib.auth.models import User
import simplejson as json
import urllib
from datetime import datetime
from reddit.api import Comment


class RedditAccount(models.Model):
    """
    Represents a User ID on Reddit

    This model can be populated by API update:

    >>> from reddit.models import RedditAccount
    >>> mod = RedditAccount()
    >>> mod.username = 'nik_doof'
    >>> mod.api_update()
    >>> mod.reddit_id
    '1axok'
    """

    user = models.ForeignKey(User, blank=True, null=True)

    username = models.CharField("Reddit Username", max_length=32, blank=False)
    reddit_id = models.CharField("Reddit ID", max_length=32)    

    link_karma = models.IntegerField("Link Karma")
    comment_karma = models.IntegerField("Comment Karma")
    validated = models.BooleanField("Validated")

    date_created = models.DateTimeField("Date Created")
    last_update = models.DateTimeField("Last Update from API")

    def api_update(self):
        try:
            jsondoc = json.load(urllib.urlopen("http://reddit.com/user/%s/about.json" % self.username))
        except:
            raise self.DoesNotExist
        
        data = jsondoc['data']
        
        self.link_karma = data['link_karma']
        self.comment_karma = data['comment_karma']
        self.reddit_id = data['id']

        self.date_created = datetime.fromtimestamp(data['created_utc'])
        self.last_update = datetime.now()

    def recent_posts(self):
        try:
            jsondoc = json.load(urllib.urlopen("http://reddit.com/user/%s.json" % self.username))
        except:
            raise self.DoesNotExist
        
        posts = []
        for item in jsondoc['data']['children']:
            if item['kind'] == 't1':
                posts.append(Comment(item['data']))
            elif item['kind'] == 't3':
                posts.append(item['data'])

        return posts


    class Meta:
        app_label = 'reddit'
        ordering = ['username']
        verbose_name = 'Reddit Account'
        verbose_name_plural = 'Reddit Accounts'

    def __unicode__(self):
        return self.username

    def __str__(self):
        return self.__unicode__()
