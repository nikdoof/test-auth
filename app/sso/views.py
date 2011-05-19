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
from django.conf import settings

from utils import installed

from eve_api.models import EVEAccount, EVEPlayerCharacter
from eve_api.tasks import import_apikey, import_apikey_result, update_user_access

from eve_proxy.models import ApiAccessLog

from sso.models import ServiceAccount, Service, SSOUser, ExistingUser, ServiceError
from sso.forms import UserServiceAccountForm, ServiceAccountResetForm, UserLookupForm, APIPasswordForm, EmailChangeForm

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

            if acc.service.settings['use_auth_username']:
                username = request.user.username
            else:
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

    if serviceid > 0:
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

    if serviceid > 0:
        try:
            acc = ServiceAccount.objects.get(id=serviceid)
        except ServiceAccount.DoesNotExist:
            return redirect('sso.views.profile')

        # If the account is inactive, or the service doesn't require a password, redirect
        if not acc.active or ('require_password' in acc.service.settings and not acc.service.settings['require_password']):
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
def user_view(request, username=None):
    """ View a user's profile as a admin """

    if not request.user.is_staff:
        return redirect('sso.views.profile')

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
        if installed('hr'):
            from hr.utils import blacklist_values
            blacklisted = len(blacklist_values(user))
        services = ServiceAccount.objects.select_related('service').filter(user=user).only('service__name', 'service_uid', 'active')
        characters = EVEPlayerCharacter.objects.select_related('corporation').filter(eveaccount__user=user).only('id', 'name', 'corporation__name')

    return render_to_response('sso/lookup/user.html', locals(), context_instance=RequestContext(request))


@login_required
def user_lookup(request):
    """ Lookup a user's account by providing a matching criteria """

    form = UserLookupForm()

    if not request.user.is_staff:
        return redirect('sso.views.profile')

    if request.method == 'POST':
        form = UserLookupForm(request.POST)
        if form.is_valid():
            users = None
            uids = []
            if form.cleaned_data['type'] == '1':
                users = User.objects.filter(username__icontains=form.cleaned_data['username']).only('username')
            elif form.cleaned_data['type'] == '2':
                uid = EVEAccount.objects.filter(characters__name__icontains=form.cleaned_data['username']).values('user')
                for u in uid:
                    uids.append(u['user'])
                users = User.objects.filter(id__in=uids).only('username')
            elif installed('reddit') and form.cleaned_data['type'] == '3':
                from reddit.models import RedditAccount
                uid = RedditAccount.objects.filter(username__icontains=form.cleaned_data['username']).values('user')
                for u in uid:
                    uids.append(u['user'])
                users = User.objects.filter(id__in=uids).only('username')
            elif form.cleaned_data['type'] == '4':
                users = User.objects.filter(email__icontains=form.cleaned_data['username']).only('username')
            elif form.cleaned_data['type'] == '5':
                uids = EVEAccount.objects.filter(api_user_id__icontains=form.cleaned_data['username']).values_list('user', flat=True)
                users = User.objects.filter(id__in=uids).only('username')
            else:
                messages.add_message(request, messages.ERROR, "Error parsing form, Type: %s, Value: %s" % (form.cleaned_data['type'], form.cleaned_data['username']))
                return redirect('sso.views.user_lookup')

            if users and len(users) == 1:
                return redirect(user_view, username=users[0].username)
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


@login_required
def refresh_access(request, userid=0):
    """ Refreshes the user's access """

    if userid > 0 and request.user.is_staff:
        update_user_access(userid)
    elif request.user:
        update_user_access(request.user.id)
        messages.add_message(request, messages.INFO, "User access updated.")
    return redirect('sso.views.profile')


@login_required
def email_change(request):
    """ Change the user's email address """

    if request.method == 'POST':
        form = EmailChangeForm(request.POST)
        if form.is_valid():
            request.user.email = form.cleaned_data['email2']
            request.user.save()
            messages.add_message(request, messages.INFO, "E-mail address changed to %s." % form.cleaned_data['email2'])
            return redirect('sso.views.profile') # Redirect after POST
    else:
        form = EmailChangeForm() # An unbound form

    return render_to_response('sso/emailchange.html', locals(), context_instance=RequestContext(request))

