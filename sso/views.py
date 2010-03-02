from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from eve_api.api_exceptions import APIAuthException, APINoUserIDException
from eve_api.api_puller.accounts import import_eve_account
from eve_api.models.api_player import EVEAccount

from sso.models import ServiceAccount, SSOUser
from sso.forms import EveAPIForm, UserServiceAccountForm, RedditAccountForm

from reddit.models import RedditAccount

import settings

def index(request):
    return render_to_response('sso/index.html')

@login_required
def profile(request):

    user = request.user
    try:
        profile = request.user.get_profile()
    except SSOUser.DoesNotExist:
        profile = SSOUser(user=request.user)
        profile.save()

    try:
        srvaccounts = ServiceAccount.objects.filter(user=request.user).all()
    except ServiceAccount.DoesNotExist:
        srvaccounts = None

    try:
        redditaccounts = RedditAccount.objects.filter(user=request.user).all()
    except ServiceAccount.DoesNotExist:
        redditaccounts = None
    
    try:
        eveaccounts = EVEAccount.objects.filter(user=request.user).all()
    except EVEAccount.DoesNotExist:
        eveaccounts = None

    return render_to_response('profile.html', locals())

@login_required
def eveapi_add(request):
    if request.method == 'POST': 
        form = EveAPIForm(request.POST) 
        if form.is_valid():
            try: 
                acc = import_eve_account(form.cleaned_data['api_key'], form.cleaned_data['user_id'])
            except APIAuthException:
                return HttpResponseRedirect(reverse('sso.views.profile'))

            acc.user = request.user
            acc.description = form.cleaned_data['description']
            acc.save()

            request.user.get_profile().update_access()

            return HttpResponseRedirect(reverse('sso.views.profile')) # Redirect after POST
    else:
        form = EveAPIForm() # An unbound form

    return render_to_response('sso/eveapi.html', {
        'form': form,
    })

@login_required
def eveapi_del(request, userid=0):

    if userid > 0 :

        try:
            acc = EVEAccount.objects.get(id=userid)
        except EVEAccount.DoesNotExist:
            return HttpResponseRedirect(reverse('sso.views.profile'))

        if acc.user == request.user:
            acc.delete()

    return HttpResponseRedirect(reverse('sso.views.profile'))

@login_required
def service_add(request):
    clsform = UserServiceAccountForm(request.user)

    if request.method == 'POST': 
        form = clsform(request.POST) 
        if form.is_valid():
  
            acc = ServiceAccount()

            acc.user = request.user

            acc.service = form.cleaned_data['service']
            acc.username = form.cleaned_data['username']
            acc.password = form.cleaned_data['password']

            acc.save()
            return HttpResponseRedirect(reverse('sso.views.profile')) # Redirect after POST
    else:
        defaults = { 'username': request.user.username, 'password': request.user.get_profile().default_service_passwd }
        form = clsform(defaults) # An unbound form

    return render_to_response('sso/serviceaccount.html', {
        'form': form,
    })

@login_required
def service_del(request, serviceid=0):
    if serviceid > 0 :

        try:
            acc = ServiceAccount.objects.get(id=serviceid)
        except ServiceAccount.DoesNotExist:
            return HttpResponseRedirect(reverse('sso.views.profile'))

        if acc.user == request.user:
            acc.delete()

    return HttpResponseRedirect(reverse('sso.views.profile'))


@login_required
def reddit_add(request):
    if request.method == 'POST': 
        form = RedditAccountForm(request.POST) 
        if form.is_valid():
  
            acc = RedditAccount()

            acc.user = request.user
            acc.username = form.cleaned_data['username']

            acc.save()
            return HttpResponseRedirect(reverse('sso.views.profile')) # Redirect after POST
    else:
        defaults = { 'username': request.user.username, }
        form = RedditAccountForm(defaults) # An unbound form

    return render_to_response('sso/redditaccount.html', {
        'form': form,
    })

@login_required
def reddit_del(request, redditid=0):
    if redditid > 0 :
        try:
            acc = RedditAccount.objects.get(id=redditid)
        except RedditAccount.DoesNotExist:
            return HttpResponseRedirect(reverse('sso.views.profile'))

        if acc.user == request.user:
            acc.delete()

    return HttpResponseRedirect(reverse('sso.views.profile'))




