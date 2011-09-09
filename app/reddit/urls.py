from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from reddit import views

urlpatterns = patterns('',
    url(r'^profile/add/reddit', login_required(views.RedditAddAccount.as_view()), name='reddit-addaccount'),
    url(r'^profile/del/reddit/(?P<slug>\d+)/$', login_required(views.RedditDeleteAccount.as_view()), name='reddit-delaccount'),
    url(r'^reddit/comments.json$', views.RedditCommentsJSON.as_view(), name='reddit-commentsjson'),
)
