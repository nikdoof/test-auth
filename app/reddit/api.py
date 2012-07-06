try:
    from django.utils import simplejson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        raise ImportError("simplejson is required for this library to work")

import urllib2
import urllib
from datetime import datetime
import unicodedata 

class NotLoggedIn(Exception):
    pass

class LoginError(Exception):
    pass

REDDIT = "http://www.reddit.com"

class RedditAPI:
    """
    Generic class for authenticated Reddit API access
    """

    REDDIT_API_LOGIN = "%s/api/login" % REDDIT

    def __init__(self, username=None, password=None):
        if username and password:
            self.login(username, password)

    @staticmethod
    def _url(api, sr=None):
        # Inspired by the offical reddit client

        if api[0] == '/':
            api = api[1:]

        if sr:
            url = '%s/r/%s/%s' % (REDDIT, sr, api)
        else:
            url = '%s/%s' % (REDDIT, api)

        return '%s.json' % url

    def login(self, username, password):
        data = { 'user': username,
                 'passwd': password,
                 'api_type': 'json' }
        url = "%s/%s" % (self.REDDIT_API_LOGIN, username)

        jsondoc = self._request(url, data, method='POST')

        if jsondoc and 'json' in jsondoc:
            if 'data' in jsondoc['json']:
                self.login_cookie = jsondoc['json']['data']['cookie']
                self.modhash = jsondoc['json']['data']['modhash']
                if self.login_cookie:
                    return True
            elif 'errors' in jsondoc['json']:
                raise LoginError(jsondoc['json']['errors'])

        return False

    @property
    def loggedin(self):
        if hasattr(self, 'login_cookie') and not self.login_cookie == '':
            return True
        return False

    def _request(self, url, data, method='GET'):
        if not hasattr(self, '_opener'):
            self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
            urllib2.install_opener(self._opener)

        data = urllib.urlencode(data)
        if method == 'GET':
            if '?' in url:
                url = '%s&%s' % (url, data)
            else:
                url = '%s?%s' % (url, data)
            data = None

        headers = {'User-Agent': 'evedreddit-auth/1.0'}
        resp = self._opener.open(urllib2.Request(url, data, headers))
        resptxt = resp.read()
        if resp.info()['Content-Type'] == 'text/plain':
            logging.info('returning plaintext')
            return resptxt
        return json.loads(resptxt)


class Comment(dict):
    """ Abstraction for comment data provided by JSON 
        Comments can be identifed by Kind = 1 """


    def __init__(self, data):

        dict.__init__(self)
        self['kind'] = 1
        self['id'] = data['id']
        self['post'] = data['link_id'][3:]
        self['body'] = data['body']
        self['ups'] = data['likes']
        self['downs'] = data['downs']
        self['subreddit_id'] = data['subreddit_id']
        self['subreddit'] = data['subreddit']
        self['author'] = data['author']
        self['permalink'] = u'http://reddit.com/comments/%s/c/%s' % (self['post'], self['id'])

    def __getattr__(self, name):
        return dict.__getitem__(self, name)

    def __unicode__(self):
        return u'/r/%s - %s' % (self['subreddit'], ['self.author'])

    def __str__(self):
        return self.__unicode__()


class Message(dict):
    """ Abstract for a Reddit Message """

    def __init__(self, msg=None):
        if msg:
            for k in msg.keys():
                self[k] = msg[k]

    def __getattr__(self, name):
        return dict.__getitem__(self, name)

    def __unicode__(self):
        return u"%s: %s" % (self.author, self.subject)

    def __str__(self):
        return self.__unicode__()


class Inbox(RedditAPI):
    """
    Reddit Inbox class, accesses a user's inbox and provides a iterable
    list of messages

    >>> inbox = Inbox(username='testuser', password='testpassword')
    >>> len(inbox)
    5

    """

    REDDIT_API_INBOX = '/message/inbox/'
    REDDIT_API_COMPOSE = '/api/compose/'

    @property
    def _inbox_data(self):

        if not self.loggedin:
            raise NotLoggedIn

        if not hasattr(self, '_inbox_cache') or not len(self._inbox_cache):
            inbox = self._request(self._url(self.REDDIT_API_INBOX), {'mark': 'false'}, method='GET')

            if inbox and 'data' in inbox:
                self._inbox_cache = []
                for msg in inbox['data']['children']:
                    self._inbox_cache.append(Message(msg['data']))
            else:
                self._inbox_cache = []
             
        return self._inbox_cache

    def __len__(self):
        return len(self._inbox_data)

    def __getitem__(self, name):
        return self._inbox_data[name]

    def __iter__(self):
        return self._inbox_data.__iter__()

    def send(self, to, subject, text):
        if not self.loggedin:
            raise NotLoggedIn

        data = { 'to': to,
                 'subject': subject.encode('utf-8'),
                 'text': text.encode('utf-8'), 
                 'uh': self.modhash,
                 'thing_id': '' }
        url = self._url(self.REDDIT_API_COMPOSE)
        jsondoc = self._request(url, data, method='POST')


class Flair(RedditAPI):
    """
    Manages a subreddit's flair list
    """

    REDDIT_API_FLAIR = "/api/flair"
    REDDIT_API_FLAIRLIST = "/api/flairlist"

    def flairlist(self, subreddit, start=None):

        if not self.loggedin:
            raise NotLoggedIn

        data = { 'r': subreddit, 'limit': 1000, 'uh': self.modhash }
        if start: data['after'] = start
        url = self._url(self.REDDIT_API_FLAIRLIST, subreddit)

        jsondoc = self._request(url, data)
        users = jsondoc['users']

        if len(users) == 1000:
            # Assume we have more to get
            users.extend(self.flairlist(subreddit, jsondoc['next']))
        return users

    def clear_flair(self, subreddit, user):
        """
        Clears a user's flair
        """
        return self.set_flair(subreddit, user, '', '')

    def set_flair(self, subreddit, user, text, css_class):

        if not self.loggedin:
            raise NotLoggedIn

        data = { 'r': subreddit, 'name': user, 'uh': self.modhash, 'text': text, 'css_class': css_class }
        url = self._url(self.REDDIT_API_FLAIR)
        jsondoc = self._request(url, data, method='POST')

        if jsondoc:
            return True
        return False
