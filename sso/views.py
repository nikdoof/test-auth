import hashlib
import random

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from eve_api.api_exceptions import APIAuthException, APINoUserIDException
from eve_api.api_puller.accounts import import_eve_account
from eve_api.models.api_player import EVEAccount, EVEPlayerCharacter

from sso.models import ServiceAccount, Service, SSOUser, ExistingUser
from sso.forms import EveAPIForm, UserServiceAccountForm, RedditAccountForm, UserLookupForm

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

    return render_to_response('sso/profile.html', locals(), context_instance=RequestContext(request))

@login_required
def characters(request, charid=0):

    if charid:
        try:
            character = EVEPlayerCharacter.objects.get(id=charid)
        except EVEPlayerCharacter.DoesNotExist:
            return HttpResponseRedirect(reverse('sso.views.profile'))
        return render_to_response('sso/character.html', locals(), context_instance=RequestContext(request))
    try:
        eveaccounts = EVEAccount.objects.filter(user=request.user).all()
        characters = []
        for acc in eveaccounts:
            chars = acc.characters.all()
            for char in chars:
                characters.append({'id': char.id, 'name': char.name, 'corp': char.corporation.name})

    except EVEAccount.DoesNotExist:
        characters = []

    return render_to_response('sso/characterlist.html', locals(), context_instance=RequestContext(request))

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
            request.user.message_set.create(message="EVE API successfully added.")

            request.user.get_profile().update_access()

            return HttpResponseRedirect(reverse('sso.views.profile')) # Redirect after POST
    else:
        form = EveAPIForm() # An unbound form

    return render_to_response('sso/eveapi.html', locals(), context_instance=RequestContext(request))

@login_required
def eveapi_del(request, userid=0):

    if userid > 0 :

        try:
            acc = EVEAccount.objects.get(id=userid)
        except EVEAccount.DoesNotExist:
            return HttpResponseRedirect(reverse('sso.views.profile'))

        if acc.user == request.user:
            acc.delete()
            request.user.message_set.create(message="EVE API key successfully deleted.")

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
            acc.character = form.cleaned_data['character']
            acc.password = hashlib.sha1('%s%s%s' % (form.cleaned_data['character'].name, settings.SECRET_KEY, random.randint(0, 2147483647))).hexdigest()

            try:
                acc.save()
            except ExistingUser:
                error = "User by this name already exists, your account has not been created"
            else:
                error = None

            return render_to_response('sso/serviceaccount/created.html', { 'account': acc, 'error': error }, context_instance=RequestContext(request))
    else:
        #defaults = { 'username': request.user.username, 'password': request.user.get_profile().default_service_passwd }

        availserv = Service.objects.filter(groups__in=request.user.groups.all()).exclude(id__in=ServiceAccount.objects.filter(user=request.user).values('service'))
        if len(availserv) == 0:
            return render_to_response('sso/serviceaccount/noneavailable.html', locals(), context_instance=RequestContext(request))
        else: 
            form = clsform() # An unbound form

    return render_to_response('sso/serviceaccount/index.html', locals())

@login_required
def service_del(request, serviceid=0):
    if serviceid > 0 :

        try:
            acc = ServiceAccount.objects.get(id=serviceid)
        except ServiceAccount.DoesNotExist:
            return HttpResponseRedirect(reverse('sso.views.profile'))

        if acc.user == request.user:
            acc.delete()
            request.user.message_set.create(message="Service account successfully deleted.")
    return HttpResponseRedirect(reverse('sso.views.profile'))

@login_required
def service_reset(request, serviceid=0, accept=0):
    if serviceid > 0 :
        try:
            acc = ServiceAccount.objects.get(id=serviceid)
        except ServiceAccount.DoesNotExist:
            return HttpResponseRedirect(reverse('sso.views.profile'))

        if acc.user == request.user:
            if not accept:
                return render_to_response('sso/serviceaccount/reset.html', locals())

            passwd = hashlib.sha1('%s%s%s' % (acc.service_uid, settings.SECRET_KEY, random.randint(0, 2147483647))).hexdigest()

            api = acc.service.api_class
            if not api.reset_password(acc.service_uid, passwd):
                error = True
            return render_to_response('sso/serviceaccount/resetcomplete.html', locals(), context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('sso.views.profile'))


@login_required
def reddit_add(request):
    if request.method == 'POST': 
        form = RedditAccountForm(request.POST) 
        if form.is_valid():
  
            acc = RedditAccount()

            acc.user = request.user
            acc.username = form.cleaned_data['username']
            acc.api_update()

            acc.save()

            request.user.message_set.create(message="Reddit account %s successfully added." % acc.username)
            return HttpResponseRedirect(reverse('sso.views.profile')) # Redirect after POST
    else:
        defaults = { 'username': request.user.username, }
        form = RedditAccountForm(defaults) # An unbound form

    return render_to_response('sso/redditaccount.html', locals())

@login_required
def reddit_del(request, redditid=0):
    if redditid > 0 :
        try:
            acc = RedditAccount.objects.get(id=redditid)
        except RedditAccount.DoesNotExist:
            return HttpResponseRedirect(reverse('sso.views.profile'))

        if acc.user == request.user:
            acc.delete()
            request.user.message_set.create(message="Reddit account successfully deleted.")

    return HttpResponseRedirect(reverse('sso.views.profile'))



@login_required
def user_view(request, user=None):
    form = UserLookupForm()

    if user:
       user = user
    elif request.method == 'POST': 
        form = UserLookupForm(request.POST) 
        if form.is_valid():
            user = form.cleaned_data['username']
        else:
            return render_to_response('sso/userlookup.html', locals())
    else:
		return render_to_response('sso/userlookup.html', locals())

    is_admin = request.user.is_staff

    user = User.objects.get(username=user)
    profile = user.get_profile()

    if is_admin:
		try:
			services = ServiceAccount.objects.filter(user=user).all()
		except ServiceAccount.DoesNotExist:
			services = None

		try:
			reddits = RedditAccount.objects.filter(user=user).all()
		except ServiceAccount.DoesNotExist:
			reddits = None

		try:
			eveaccounts = EVEAccount.objects.filter(user=user).all()

			characters = []

			for acc in eveaccounts:
				chars = acc.characters.all()
				for char in chars:
					characters.append({'name': char.name, 'corp': char.corporation.name})

		except EVEAccount.DoesNotExist:
			eveaccounts = None

    return render_to_response('sso/user.html', locals())
