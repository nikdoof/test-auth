from django.views.generic import TemplateView, DeleteView, CreateView
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson as json
from django.core.urlresolvers import reverse

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from reddit.forms import RedditAccountForm
from reddit.models import RedditAccount

class RedditAddAccount(CreateView):
    """
    Adds a reddit account to the system
    """

    model = RedditAccount
    template_name = 'reddit/add.html'
    form_class = RedditAccountForm

    def get_success_url(self):
        return reverse('sso.views.profile')

    def get_initial(self):
        initial = super(RedditAddAccount, self).get_initial()
        initial['username'] = self.request.user.username
        initial['user'] = self.request.user
        return initial

    def form_valid(self, form):
        acc = form.save(commit=False)
        acc.user = self.request.user
        try:
            acc.api_update()
        except RedditAccount.DoesNotExist:
            messages.add_message(self.request, messages.ERROR, "Error, user %s does not exist on Reddit" % acc.username )
        else:
            acc.save()
            messages.add_message(self.request, messages.INFO, "Reddit account %s successfully added." % acc.username)
        return HttpResponseRedirect(self.get_success_url())


class RedditDeleteAccount(DeleteView):
    """
    Deletes an existing Reddit account stored in the system
    """

    slug_field = 'id'
    model = RedditAccount
    template_name = 'reddit/delete.html'
    context_object_name = 'account'

    def get_success_url(self):
        return reverse('sso.views.profile')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user == self.request.user:
            self.object.delete()
            messages.add_message(self.request, messages.INFO, "Reddit account successfully deleted.")
        return HttpResponseRedirect(self.get_success_url())


class JSONResponseMixin(object):
    """
    Renders the template context as a JSON response
    """

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
