from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.generic import TemplateView
from django.http import HttpResponse
import django.utils.simplejson as json

from django.contrib import messages
from django.contrib.auth.models import User
from gargoyle.decorators import switch_is_active

from reddit.forms import RedditAccountForm
from reddit.models import RedditAccount

@login_required
@switch_is_active('reddit')
def reddit_add(request):
    """ Add a Reddit account to a user's account """

    if request.method == 'POST':
        form = RedditAccountForm(request.POST)
        if form.is_valid():
            acc = RedditAccount()
            acc.user = request.user
            acc.username = form.cleaned_data['username']
            try:
                acc.api_update()
            except RedditAccount.DoesNotExist:
                messages.add_message(request, messages.ERROR, "Error, user %s does not exist on Reddit" % acc.username )
                return render_to_response('reddit/add_reddit_account.html', locals(), context_instance=RequestContext(request))
            acc.save()

            messages.add_message(request, messages.INFO, "Reddit account %s successfully added." % acc.username)
            return redirect('sso.views.profile') # Redirect after POST
    else:
        defaults = { 'username': request.user.username, }
        form = RedditAccountForm(defaults) # An unbound form

    return render_to_response('reddit/add_reddit_account.html', locals(), context_instance=RequestContext(request))

@login_required
@switch_is_active('reddit')
def reddit_del(request, redditid=0):
    """ Delete a Reddit account from a user's account """

    if redditid > 0 :
        try:
            acc = RedditAccount.objects.get(id=redditid)
        except RedditAccount.DoesNotExist:
            return redirect('sso.views.profile')

        if acc.user == request.user:
            acc.delete()
            messages.add_message(request, messages.INFO, "Reddit account successfully deleted.")

    return redirect('sso.views.profile')


class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return HttpResponse(content,
                            content_type='application/json',
                            **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context)


class RedditCommentsJSON(JSONResponseMixin, TemplateView):

    def dispatch(self, request, *args, **kwargs):
        self.user = User.objects.get(id=request.GET.get('userid'))
        return super(RedditCommentsJSON, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        posts = []
        for account in self.user.redditaccount_set.all():
            try:
                accposts = account.recent_posts()
            except:
                accposts = []
            posts.extend(accposts)
        return {'posts': posts}
