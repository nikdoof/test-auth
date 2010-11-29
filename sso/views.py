import hashlib
import random
import re
import unicodedata
import celery

from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core import serializers

from eve_api.api_exceptions import APIAuthException, APINoUserIDException
from eve_api.api_puller.accounts import import_eve_account
from eve_api.models.api_player import EVEAccount, EVEPlayerCharacter
from eve_proxy.models import ApiAccessLog
from sso.models import ServiceAccount, Service, SSOUser, ExistingUser, ServiceError
from sso.forms import EveAPIForm, UserServiceAccountForm, ServiceAccountResetForm, RedditAccountForm, UserLookupForm, APIPasswordForm
from reddit.models import RedditAccount

from eve_api.tasks import import_apikey

import settings

def index(request):
    if request.user:
        return redirect('sso.views.profile')
    else:
        return render_to_response('sso/index.html', context_instance=RequestContext(request))

@login_required
def profile(request):
    """ Displays the user's profile page """

    user = request.user
    try:
        profile = request.user.get_profile()
    except SSOUser.DoesNotExist:
        profile = SSOUser(user=request.user)
        profile.save()

    return render_to_response('sso/profile.html', locals(), context_instance=RequestContext(request))

@login_required
def characters(request, charid=0):
    """ Provide a list of characters, or a indivdual character sheet """

    if charid:
        character = get_object_or_404(EVEPlayerCharacter.objects.select_related('corporation', 'corporation__aliance'), id=charid)
        return render_to_response('sso/character.html', locals(), context_instance=RequestContext(request))

    characters = EVEPlayerCharacter.objects.select_related('corporation', 'corporation__alliance').filter(eveaccount__user=request.user).only('id', 'name', 'corporation__name', 'corporation__alliance__name')
    return render_to_response('sso/characterlist.html', locals(), context_instance=RequestContext(request))

@login_required
def eveapi_add(request):
    """ Add a EVE API key to a user's account """

    if request.method == 'POST': 
        form = EveAPIForm(request.POST) 
        if form.is_valid():

            task = import_apikey.delay(api_key=form.cleaned_data['api_key'], api_userid=form.cleaned_data['user_id'], user=request.user.id)
            try:
                task.wait(5)
            except celery.exceptions.TimeoutError:
                messages.add_message(request, messages.INFO, "The addition of your API key is still processing, please check back in a minute or so")
                pass    
            else:
                messages.add_message(request, messages.INFO, "EVE API successfully added.")

            return redirect('sso.views.profile')
    else:
        form = EveAPIForm() # An unbound form

    return render_to_response('sso/eveapi.html', locals(), context_instance=RequestContext(request))

@login_required
def eveapi_del(request, userid=0):
    """ Delete a EVE API key from a account """

    if userid > 0 :
        try:
            acc = EVEAccount.objects.get(id=userid)
        except EVEAccount.DoesNotExist:
            return redirect('sso.views.profile')
        if acc.user == request.user:
            acc.delete()
            messages.add_message(request, messages.INFO, "EVE API key successfully deleted.")

    return redirect('sso.views.profile')

@login_required
def eveapi_refresh(request, userid=0):
    """ Force refresh a EVE API key """

    if userid > 0 :
        try:
            acc = EVEAccount.objects.get(id=userid)
        except EVEAccount.DoesNotExist:
            pass
        else:
            if acc.user == request.user or request.user.is_superuser:
                task = import_apikey.delay(api_key=acc.api_key, api_userid=acc.api_user_id, force_cache=True, user=request.user.id)

                if request.is_ajax():
                    try:
                        acc = task.wait(30)
                        return HttpResponse(serializers.serialize('json', [acc]), mimetype='application/javascript')
                    except celery.exceptions.TimeoutError:
                        return HttpResponse(serializers.serialize('json', []), mimetype='application/javascript')
                else:
                    messages.add_message(request, messages.INFO,"Key %s has been queued to be refreshed from the API" % acc.api_user_id)

    return redirect('sso.views.profile')

@login_required
def eveapi_log(request, userid=0):
    """ Provides a list of access logs for a specific EVE API key """
    if userid > 0 :
        try:
            acc = EVEAccount.objects.get(id=userid)
        except:
            pass

        if acc and (acc.user == request.user or request.user.is_staff):
            logs = ApiAccessLog.objects.filter(userid=userid).order_by('-time_access')[:50]
            return render_to_response('sso/eveapi_log.html', locals(), context_instance=RequestContext(request))

        return redirect('sso.views.profile')

@login_required
def service_add(request):
    """ Add a service to a user's account """

    clsform = UserServiceAccountForm(request.user)

    if request.method == 'POST': 
        form = clsform(request.POST) 
        if form.is_valid():

            acc = ServiceAccount(user=request.user, service=form.cleaned_data['service'])
            acc.character = form.cleaned_data['character']

            if acc.service.settings['require_password']:
                if settings.GENERATE_SERVICE_PASSWORD:
                    acc.password = hashlib.sha1('%s%s%s' % (form.cleaned_data['character'].name, settings.SECRET_KEY, random.randint(0, 2147483647))).hexdigest()
                else:
                    acc.password = form.cleaned_data['password']
            else:
                acc.password = None

            # Decode unicode and remove invalid characters
            username = re.sub('[^a-zA-Z0-9_-]+', '', unicodedata.normalize('NFKD', acc.character.name).encode('ASCII', 'ignore'))

            if acc.service.api_class.check_user(username):
                error = "Username already exists on the target service, please contact an admin."
            else:
                ret = acc.service.api_class.add_user(username, acc.password, user=request.user, character=acc.character)
                if ret:
                    acc.service_uid = ret['username']
                    acc.save()
                    error = None
                else:
                    error = "Error creating account on the service, please retry or contact an admin if the error persists."

            return render_to_response('sso/serviceaccount/created.html', locals(), context_instance=RequestContext(request))

    else:
        availserv = Service.objects.filter(groups__in=request.user.groups.all()).exclude(id__in=ServiceAccount.objects.filter(user=request.user).values('service'))
        if len(availserv) == 0:
            return render_to_response('sso/serviceaccount/noneavailable.html', locals(), context_instance=RequestContext(request))
        else: 
            form = clsform() # An unbound form

    return render_to_response('sso/serviceaccount/index.html', locals())

@login_required
def service_del(request, serviceid=0):
    """ Delete a service from a user's account """

    if serviceid > 0 :
        try:
            acc = ServiceAccount.objects.get(id=serviceid)
        except ServiceAccount.DoesNotExist:
            return redirect('sso.views.profile')

        if not acc.user == request.user:
            return redirect('sso.views.profile')

        if request.method == 'POST':
            if 'confirm-delete' in request.POST:
                try:
                    acc.delete()
                except ServiceError:
                    messages.add_message(request, messages.ERROR, "Error deleting the service account, try again later.")
                else:
                    messages.add_message(request, messages.INFO, "Service account successfully deleted.")
        else:
            return render_to_response('sso/serviceaccount/deleteconfirm.html', locals(), context_instance=RequestContext(request))

    return redirect('sso.views.profile')

@login_required
def service_reset(request, serviceid=0):
    """ Reset a user's password on a service """

    if serviceid > 0 :
        try:
            acc = ServiceAccount.objects.get(id=serviceid)
        except ServiceAccount.DoesNotExist:
            return redirect('sso.views.profile')

        if not acc.active:
            return redirect('sso.views.profile')

        if acc.user == request.user:
            if not request.method == 'POST':
                form = ServiceAccountResetForm()
                return render_to_response('sso/serviceaccount/reset.html', locals(), context_instance=RequestContext(request))

            form = ServiceAccountResetForm(request.POST)
            if form.is_valid():
                if settings.GENERATE_SERVICE_PASSWORD:
                    passwd = hashlib.sha1('%s%s%s' % (acc.service_uid, settings.SECRET_KEY, random.randint(0, 2147483647))).hexdigest()
                else:
                    passwd = form.cleaned_data['password']

                api = acc.service.api_class
                if not api.reset_password(acc.service_uid, passwd):
                    error = True
                return render_to_response('sso/serviceaccount/resetcomplete.html', locals(), context_instance=RequestContext(request))
            else:
                return render_to_response('sso/serviceaccount/reset.html', locals(), context_instance=RequestContext(request))

    return redirect('sso.views.profile')

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
                return render_to_response('sso/redditaccount.html', locals(), context_instance=RequestContext(request))
            acc.save()

            messages.add_message(request, messages.INFO, "Reddit account %s successfully added." % acc.username)
            return redirect('sso.views.profile') # Redirect after POST
    else:
        defaults = { 'username': request.user.username, }
        form = RedditAccountForm(defaults) # An unbound form

    return render_to_response('sso/redditaccount.html', locals(), context_instance=RequestContext(request))

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

@login_required
def user_view(request, username=None):
    """ View a user's profile as a admin """

    if username:
       try:
           user = User.objects.get(username=username)
       except User.DoesNotExist:
           return redirect('sso.views.user_lookup')
    else:
       return redirect('sso.views.user_lookup')

    profile = user.get_profile()
    is_admin = request.user.is_staff
    if is_admin:
        services = ServiceAccount.objects.select_related('service').filter(user=user).only('service__name', 'service_uid', 'active')
        reddits = RedditAccount.objects.filter(user=user).all()
        characters = EVEPlayerCharacter.objects.select_related('corporation').filter(eveaccount__user=user).only('id', 'name', 'corporation__name')

    return render_to_response('sso/lookup/user.html', locals(), context_instance=RequestContext(request))

@login_required
def user_lookup(request):
    """ Lookup a user's account by providing a matching criteria """

    form = UserLookupForm()

    if request.method == 'POST':
        form = UserLookupForm(request.POST)
        if form.is_valid():
            users = None
            uids = []
            if form.cleaned_data['type'] == '1':
                users = User.objects.filter(username__icontains=form.cleaned_data['username']).only('username')
            elif form.cleaned_data['type'] == '2':
                uid = EVEAccount.objects.filter(characters__name__icontains=form.cleaned_data['username']).values('user')
                for u in uid: uids.append(u['user'])
                users = User.objects.filter(id__in=uids).only('username')
            elif form.cleaned_data['type'] == '3':
                uid = RedditAccount.objects.filter(username__icontains=form.cleaned_data['username']).values('user')
                for u in uid: uids.append(u['user'])
                users = User.objects.filter(id__in=uids).only('username')
            elif form.cleaned_data['type'] == '4':
                users = User.objects.filter(email__icontains=form.cleaned_data['username']).only('username')
            else:
                messages.add_message(request, messages.ERROR, "Error parsing form, Type: %s, Value: %s" % (form.cleaned_data['type'], form.cleaned_data['username']))
                return redirect('sso.views.user_lookup')

            if users and len(users) == 1:
                return redirect(user_view, args=[users[0].username])
            elif users and len(users) > 1:
                return render_to_response('sso/lookup/lookuplist.html', locals(), context_instance=RequestContext(request))
            else:
                messages.add_message(request, messages.INFO, "No results found")
                return redirect('sso.views.user_lookup')
            
    return render_to_response('sso/lookup/userlookup.html', locals(), context_instance=RequestContext(request))


@login_required
def set_apipasswd(request):
    """ Sets the user's auth API password """

    if request.method == 'POST':
        form = APIPasswordForm(request.POST)
        if form.is_valid():
            profile = request.user.get_profile()
            profile.api_service_password = hashlib.sha1(form.cleaned_data['password']).hexdigest()
            profile.save()
            messages.add_message(request, messages.INFO, "Your API Services password has been set.")
            return redirect('sso.views.profile') # Redirect after POST
    else:
        form = APIPasswordForm() # An unbound form

    return render_to_response('sso/apipassword.html', locals(), context_instance=RequestContext(request))

