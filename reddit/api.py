import simplejson as json
import urllib2
import urllib
from datetime import datetime

class NotLoggedIn(Exception):
    pass

class Message(dict):
    """ Reddit Message """

    def __init__(self, dict=None):
        if dict:
            self.dictitems = dict

    def __getattr__(self, name):
        return self.dictitems[name]

    def __unicode__(self):
        return u"%s: %s" % (self.author, self.subject)

    def __str__(self):
        return self.__unicode__()

class Inbox():
    """ Reddit Inbox class, accesses a user's inbox and provides a iterable 
        list of messages """    

    REDDIT = "http://www.reddit.com"
    REDDIT_API_LOGIN = "%s/api/login" % REDDIT
    REDDIT_API_INBOX = "%s/message/inbox/.json?mark=false" % REDDIT
    REDDIT_API_COMPOSE = "%s/api/compose/" % REDDIT

    def __init__(self, username=None, password=None):
        if username and password:
            self.login(username, password)

    def login(self, username, password):
        data = { 'user': username,
                 'passwd': password, 
                 'api_type': 'json' }
        url = "%s/%s" % (self.REDDIT_API_LOGIN, username)

        jsondoc = json.load(self._url_request(url, data))

        self.login_cookie = jsondoc['json']['data']['cookie']
        self.modhash = jsondoc['json']['data']['modhash']

        if self.login_cookie:
            return True
        return False            

    @property
    def _inbox_data(self):

        if not hasattr(self, '__inbox_cache'):
            inbox = json.load(self._opener.open(self.REDDIT_API_INBOX))['data']
            
            self.__inbox_cache = []
            for msg in inbox['children']:
                self.__inbox_cache.append(Message(msg['data']))
             
        return self.__inbox_cache

    def _url_request(self, url, data):
        if not hasattr(self, '_opener'):
            self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
            urllib2.install_opener(self._opener)

        req = urllib2.Request( url, urllib.urlencode(data))
        return self._opener.open(req)

    def __len__(self):
        return len(self._inbox_data)

    def __getitem__(self, name):
        return self._inbox_data[name]

    def __iter__(self):
        return self._inbox_data.__iter__()

    def send(self, to, subject, text):
        if not self.login_cookie:
            raise NotLoggedIn

        data = { 'to': to,
                 'subject': subject,
                 'text': text, 
                 'uh': self.modhash,
                 'thing_id': '' }
        url = "%s" % (self.REDDIT_API_COMPOSE)

        jsondoc = json.load(self._url_request(url, data))
