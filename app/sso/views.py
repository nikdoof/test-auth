import hashlib
import random
import re
import unicodedata
import celery

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core import serializers
from django.conf import settings
from django.views.generic import FormView

from gargoyle import gargoyle
from gargoyle.decorators import switch_is_active

from utils import installed
from eve_api.models import EVEAccount, EVEPlayerCharacter
from eve_api.tasks import import_apikey, import_apikey_result, update_user_access
from eve_proxy.models import ApiAccessLog
from reddit.tasks import update_user_flair
from sso.models import ServiceAccount, Service, SSOUser, ExistingUser, ServiceError
from sso.forms import UserServiceAccountForm, ServiceAccountResetForm, UserLookupForm, APIPasswordForm, EmailChangeForm, PrimaryCharacterForm, UserNoteForm

@login_required
def profile(request):
    """ Displays the user's profile page """

    try:
        profile = request.user.get_profile()
    except SSOUser.DoesNotExist:
        profile = SSOUser(user=request.user)
        profile.save()

    if not profile.primary_character and EVEPlayerCharacter.objects.filter(eveaccount__user=request.user).count():
        return redirect('sso.views.primarychar_change')

    context = {
        'profile': request.user.get_profile()
    }
    return render_to_response('sso/profile.html', context, context_instance=RequestContext(request))


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

    return render_to_response('sso/serviceaccount/add.html', locals(), context_instance=RequestContext(request))


@login_required
def service_del(request, serviceid=0, confirm_template='sso/serviceaccount/deleteconfirm.html'):
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
            return render_to_response(confirm_template, locals(), context_instance=RequestContext(request))

    return redirect('sso.views.profile')


@login_required
def service_reset(request, serviceid, template='sso/serviceaccount/reset.html', complete_template='sso/serviceaccount/resetcomplete.html'):
    """ Reset a user's password on a service """

    acc = get_object_or_404(ServiceAccount, id=serviceid)

    # If the account is inactive, or the service doesn't require a password, redirect
    if not acc.active or ('require_password' in acc.service.settings and not acc.service.settings['require_password']):
        return redirect('sso.views.profile')

    # Check if the ServiceAccount belongs to the requesting user
    if not acc.user == request.user:
        return redirect('sso.views.profile')

    if request.method == 'POST':
        form = ServiceAccountResetForm(request.POST)
        if form.is_valid():
            if settings.GENERATE_SERVICE_PASSWORD:
                passwd = hashlib.sha1('%s%s%s' % (acc.service_uid, settings.SECRET_KEY, random.randint(0, 2147483647))).hexdigest()
            else:
                passwd = form.cleaned_data['password']

            if not acc.service.api_class.reset_password(acc.service_uid, passwd):
                error = True
            return render_to_response(complete_template, locals(), context_instance=RequestContext(request))
    else:
        form = ServiceAccountResetForm()

    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def user_view(request, username, template='sso/lookup/user.html'):
    """ View a user's profile as a admin """

    if not request.user.has_perm('sso.can_view_users') and not request.user.has_perm('sso.can_view_users_restricted'):
        return redirect('sso.views.profile')

    user = get_object_or_404(User, username=username)

    context = {
        'user': user,
        'profile': user.get_profile(),
        'services':  ServiceAccount.objects.select_related('service').filter(user=user).only('service__name', 'service_uid', 'active'),
        'characters': EVEPlayerCharacter.objects.select_related('corporation').filter(eveaccount__user=user).only('id', 'name', 'corporation__name'),
    }

    # If the HR app is installed, check the blacklist
    if installed('hr'):
        if request.user.has_perm('hr.add_blacklist'):
            from hr.utils import blacklist_values
            context['blacklisted'] = len(blacklist_values(user))

    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def user_lookup(request):
    """ Lookup a user's account by providing a matching criteria """

    form = UserLookupForm(request=request)

    if not request.user.has_perm('sso.can_search_users'):
        return redirect('sso.views.profile')

    if request.method == 'POST':
        form = UserLookupForm(request.POST, request=request)
        if form.is_valid():
            users = None
            uids = []
            username = form.cleaned_data['username'].strip()
            if form.cleaned_data['type'] == '1':
                users = User.objects.filter(username__icontains=username).only('username')
            elif form.cleaned_data['type'] == '2':
                uid = EVEAccount.objects.filter(characters__name__icontains=username).values('user')
                for u in uid:
                    uids.append(u['user'])
                users = User.objects.filter(id__in=uids).only('username')
            elif installed('reddit') and gargoyle.is_active('reddit', request) and form.cleaned_data['type'] == '3':
                from reddit.models import RedditAccount
                uid = RedditAccount.objects.filter(username__icontains=username).values('user')
                for u in uid:
                    uids.append(u['user'])
                users = User.objects.filter(id__in=uids).only('username')
            elif form.cleaned_data['type'] == '4':
                users = User.objects.filter(email__icontains=username).only('username')
            elif form.cleaned_data['type'] == '5':
                uids = EVEAccount.objects.filter(api_user_id__icontains=username).values_list('user', flat=True)
                users = User.objects.filter(id__in=uids).only('username')
            else:
                messages.add_message(request, messages.ERROR, "Error parsing form, Type: %s, Value: %s" % (form.cleaned_data['type'], username))
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

    if userid > 0 and request.user.has_perm('sso.can_refresh_users'):
        u = get_object_or_404(User, id=userid)
        update_user_access(u.id)
        messages.add_message(request, messages.INFO, "%s's access has been updated." % u.username)
        return redirect(user_view, username=u.username)
    else:
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

@login_required
def primarychar_change(request):
    """ Change the user's primary character """

    if request.method == 'POST':
        form = PrimaryCharacterForm(request.POST, user=request.user)
        if form.is_valid():
            profile = request.user.get_profile()
            profile.primary_character = form.cleaned_data['character']
            profile.save()
            messages.add_message(request, messages.INFO, "Your primary character has changed to %s." % form.cleaned_data['character'])
            return redirect('sso.views.profile') # Redirect after POST
    else:
        form = PrimaryCharacterForm(initial={'character': request.user.get_profile().primary_character}, user=request.user) # An unbound form

    return render_to_response('sso/primarycharchange.html', locals(), context_instance=RequestContext(request))


@login_required
@switch_is_active('reddit')
def toggle_reddit_tagging(request):
    profile = request.user.get_profile()
    if profile.primary_character:
        profile.tag_reddit_accounts = not profile.tag_reddit_accounts
        profile.save()
        if profile.tag_reddit_accounts:
            tag = 'Enabled'
        else:
            tag = 'Disabled'
        messages.add_message(request, messages.INFO, "Reddit account tagging is now %s" % tag)

        if profile.tag_reddit_accounts:
            name = profile.primary_character.name
        else:
            name = ''
        for acc in request.user.redditaccount_set.all():
            update_user_flair.delay(acc.username, name)
    else:
        messages.add_message(request, messages.ERROR, "You need to set a primary character before using this feature!")

    return redirect('sso.views.profile')


class AddUserNote(FormView):

    template_name = 'sso/add_usernote.html'
    form_class = UserNoteForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('add_ssousernote'):
            return HttpResponseForbidden()
        return super(AddUserNote, self).dispatch(request, *args, **kwargs)

    def get_user(self):
        if not hasattr(self, 'user'):
            userid = self.kwargs.get('username', None)
            self.user = User.objects.get(username=userid)
        return self.user

    def get_context_data(self, **kwargs):
        ctx = super(AddUserNote, self).get_context_data(**kwargs)
        ctx['user'] = self.get_user()
        return ctx

    def get_initial(self):
        initial = super(AddUserNote, self).get_initial()
        initial['user'] = self.get_user()
        return initial

    def get_success_url(self):
        return reverse('sso-viewuser', args=[self.get_user()])

    def form_valid(self, form):

        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()

        return super(AddUserNote, self).form_valid(form)
