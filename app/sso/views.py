import hashlib
import random
import re
import unicodedata

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings
from django.views.generic import View, FormView, ListView, DetailView, TemplateView
from django.http import HttpResponseRedirect

import celery
from gargoyle import gargoyle
from braces.views import LoginRequiredMixin

from utils import installed
from eve_api.models import EVEAccount, EVEPlayerCharacter
from eve_api.tasks import import_apikey, import_apikey_result, update_user_access
from eve_proxy.models import ApiAccessLog
from sso.models import ServiceAccount, Service, SSOUser, ExistingUser, ServiceError, SSOUserIPAddress
from sso.forms import UserServiceAccountForm, ServiceAccountResetForm, UserLookupForm, APIPasswordForm, EmailChangeForm, PrimaryCharacterForm, UserNoteForm


class ProfileView(LoginRequiredMixin, TemplateView):

    template_name = 'sso/profile.html'

    def get_profile(self, user):
        try:
            profile = user.get_profile()
        except SSOUser.DoesNotExist:
            profile = SSOUser.objects.create(user=user)
        return profile

    def get(self, request, *args, **kwargs):
        self.profile = self.get_profile(request.user)
        if self.profile.primary_character is None and EVEPlayerCharacter.objects.filter(eveaccount__user=request.user).count():
            return HttpResponseRedirect(reverse('sso-primarycharacterupdate'))
        return super(ProfileView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ProfileView, self).get_context_data(**kwargs)
        ctx.update({
            'profile': self.profile,
            'available_services': Service.objects.filter(groups__in=self.request.user.groups.all()).exclude(id__in=ServiceAccount.objects.filter(user=self.request.user).values('service')).count()
        })
        return ctx


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
        availserv = Service.objects.filter(groups__in=request.user.groups.all()).exclude(id__in=ServiceAccount.objects.filter(user=request.user).values('service')).count()
        if not availserv:
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
            return redirect('sso-profile')

        if not acc.user == request.user:
            return redirect('sso-profile')

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

    return redirect('sso-profile')


@login_required
def service_reset(request, serviceid, template='sso/serviceaccount/reset.html', complete_template='sso/serviceaccount/resetcomplete.html'):
    """ Reset a user's password on a service """

    acc = get_object_or_404(ServiceAccount, id=serviceid)

    # If the account is inactive, or the service doesn't require a password, redirect
    if not acc.active or ('require_password' in acc.service.settings and not acc.service.settings['require_password']):
        return redirect('sso-profile')

    # Check if the ServiceAccount belongs to the requesting user
    if not acc.user == request.user:
        return redirect('sso-profile')

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


class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_url_kwarg = 'username'
    slug_field = 'username'
    template_name = 'sso/lookup/user.html'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('sso.can_view_users') and not request.user.has_perm('sso.can_view_users_restricted'):
            return HttpResponseForbidden()
        return super(UserDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(UserDetailView, self).get_context_data(**kwargs)
        ctx.update({
            'profile': self.object.get_profile(),
            'services':  ServiceAccount.objects.select_related('service').filter(user=self.object).only('service__name', 'service_uid', 'active'),
            'characters': EVEPlayerCharacter.objects.select_related('corporation', 'corporation__alliance').filter(eveaccount__user=self.object).only('id', 'name', 'corporation__name'),
        })

        # If the HR app is installed, check the blacklist
        if installed('hr'):
            if self.request.user.has_perm('hr.add_blacklist'):
                from hr.utils import blacklist_values
                output = blacklist_values(self.object)
                ctx.update({
                    'blacklisted': bool(len(output)),
                    'blacklist_items': output,
                })

        return ctx


@login_required
def user_lookup(request):
    """ Lookup a user's account by providing a matching criteria """

    form = UserLookupForm(request=request)

    if not request.user.has_perm('sso.can_search_users'):
        return redirect('sso-profile')

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
                return redirect('sso-viewuser', username=users[0].username)
            elif users and len(users) > 1:
                return render_to_response('sso/lookup/lookuplist.html', locals(), context_instance=RequestContext(request))
            else:
                messages.add_message(request, messages.INFO, "No results found")
                return redirect('sso.views.user_lookup')

    return render_to_response('sso/lookup/userlookup.html', locals(), context_instance=RequestContext(request))


class APIPasswordUpdateView(LoginRequiredMixin, FormView):

    form_class = APIPasswordForm
    template_name = 'sso/apipassword.html'
    success_url = reverse_lazy('sso-profile')

    def form_valid(self, form):
        profile = self.request.user.get_profile()
        profile.api_service_password = hashlib.sha1(form.cleaned_data['password']).hexdigest()
        profile.save()
        messages.success(self.request, "Your API services password has been updated.")
        return super(APIPasswordUpdateView, self).form_valid(form)


@login_required
def refresh_access(request, userid=0, corpid=0, allianceid=0):
    """ Refreshes the user's access """

    if userid > 0 and request.user.has_perm('sso.can_refresh_users'):
        u = get_object_or_404(User, id=userid)
        update_user_access(u.id)
        messages.add_message(request, messages.INFO, "%s's access has been updated." % u.username)
        return redirect(user_view, username=u.username)
    if corpid > 0 and request.user.has_perm('sso.can_refresh_users'):
        users = User.objects.filter(eveaccount__characters__corporation__id=corpid).distinct()
        for u in users:
            update_user_access.delay(u.id)
        messages.add_message(request, messages.INFO, "%s accounts queued for update." % users.count())
        return redirect('eveapi-corporation', pk=corpid)
    if allianceid > 0 and request.user.has_perm('sso.can_refresh_users'):
        users = User.objects.filter(eveaccount__characters__corporation__alliance__id=allianceid).distinct()
        for u in users:
            update_user_access.delay(u.id)
        messages.add_message(request, messages.INFO, "%s accounts queued for update." % users.count())
        return redirect('eveapi-alliance', pk=allianceid)
    else:
        update_user_access(request.user.id)
        messages.add_message(request, messages.INFO, "User access updated.")
        return redirect('sso-profile')


class EmailUpdateView(LoginRequiredMixin, FormView):
    """Updates a user's email address"""

    form_class = EmailChangeForm
    template_name = 'sso/emailchange.html'
    success_url = reverse_lazy('sso-profile')

    def form_valid(self, form):
        self.request.user.email = form.cleaned_data['email2']
        self.request.user.save()
        messages.success(self.request, "E-mail address changed to %s." % form.cleaned_data['email2'])
        return super(EmailUpdateView).form_valid(form)


class PrimaryCharacterUpdateView(LoginRequiredMixin, FormView):
    """Updates a user's primary character selection"""

    form_class = PrimaryCharacterForm
    template_name = 'sso/primarycharchange.html'
    success_url = reverse_lazy('sso-profile')

    def get_form_kwargs(self):
        kwargs = super(PrimaryCharacterUpdateView, self).get_form_kwargs()
        kwargs.update({
            'user': self.request.user
        })
        return kwargs

    def get_initial(self):
        initial = super(PrimaryCharacterUpdateView, self).get_initial()
        initial.update({
            'character': self.request.user.get_profile().primary_character
        })
        return initial

    def form_valid(self, form):
        profile = self.request.user.get_profile()
        profile.primary_character = form.cleaned_data['character']
        profile.save()
        messages.success(self.request, "Your primary character has changed to %s." % form.cleaned_data['character'])
        return super(PrimaryCharacterUpdateView, self).form_valid(form)


class RedditTaggingUpdateView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if not gargoyle.is_active('reddit', request):
            return HttpResponseNotFound()

        profile = request.user.get_profile()

        if profile.primary_character is None:
            messages.error("Reddit account tagging requires a primary character before using. Please set one.")
            if EVEPlayerCharacter.objects.filter(eveaccount__user=self.request.user).count():
                return HttpResponseRedirect(reverse('sso-primarycharacterupdate'))
            else:
                return HttpResponseRedirect(reverse('sso-profile'))
        profile.tag_reddit_accounts = not profile.tag_reddit_accounts
        profile.save()
        if profile.tag_reddit_accounts:
            tag = 'Enabled'
        else:
            tag = 'Disabled'
        messages.info(request, "Reddit account tagging is now %s" % tag)

        if profile.tag_reddit_accounts:
            name = profile.primary_character.name
        else:
            name = ''
        for acc in self.request.user.redditaccount_set.all():
            from reddit.tasks import update_user_flair
            update_user_flair.delay(acc.username, name)
        return HttpResponseRedirect(reverse('sso-profile'))


class AddUserNote(LoginRequiredMixin, FormView):

    template_name = 'sso/add_usernote.html'
    form_class = UserNoteForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.has_perm('sso.add_ssousernote'):
            return HttpResponseForbidden()
        return super(AddUserNote, self).dispatch(request, *args, **kwargs)

    def get_user(self):
        if not hasattr(self, 'user'):
            userid = self.kwargs.get('username', None)
            self.user = User.objects.get(username=userid)
        return self.user

    def get_context_data(self, **kwargs):
        ctx = super(AddUserNote, self).get_context_data(**kwargs)
        ctx.update({
            'user': self.get_user()
        })
        return ctx

    def get_initial(self):
        initial = super(AddUserNote, self).get_initial()
        initial.update({
            'user': self.get_user()
        })
        return initial

    def get_success_url(self):
        return reverse('sso-viewuser', args=[self.get_user()])

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()
        return super(AddUserNote, self).form_valid(form)


class UserIPAddressView(LoginRequiredMixin, ListView):

    model = SSOUserIPAddress

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('sso.can_view_users_restricted'):
            return HttpResponseForbidden()
        return super(UserIPAddressView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.GET.has_key('user'):
            qs = self.model.objects.filter(user__username__exact=self.request.GET.get('user'))
        else:
            qs = self.model.objects.filter(ip_address__contains=self.request.GET.get('ip', ''))
        return qs.order_by('-last_seen')

    def get_context_data(self, **kwargs):
        ctx = super(UserIPAddressView, self).get_context_data(**kwargs)
        ctx.update({
            'ip': self.request.GET.get('ip', None),
            'kuser': self.request.GET.get('user', None),
        })
        return ctx
