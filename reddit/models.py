from django.db import models
from django.contrib.auth.models import User
import simplejson as json
import urllib
from datetime import datetime

class RedditAccount(models.Model):
    """
    Represents a User ID on Reddit
    """

    user = models.ForeignKey(User, blank=True, null=True)

    username = models.CharField("Username", max_length=32, blank=False)
    reddit_id = models.CharField("Reddit ID", max_length=32, blank=True)    

    date_created = models.DateTimeField("Date Created", blank=True)

    link_karma = models.IntegerField("Link Karma", blank=True, null=True)
    comment_karma = models.IntegerField("Comment Karma", blank=True, null=True)

    last_update = models.DateTimeField("Last Update from API", blank=False)

    def save(self):
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
        
        return models.Model.save(self)    

    class Meta:
        app_label = 'reddit'
        ordering = ['username']
        verbose_name = 'Reddit Account'
        verbose_name_plural = 'Reddit Accounts'

    def __unicode__(self):
        return self.username

    def __str__(self):
        return self.__unicode__()
