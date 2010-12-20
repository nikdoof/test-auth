from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib import messages

from reddit.forms import RedditAccountForm
from reddit.models import RedditAccount

@login_required
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

