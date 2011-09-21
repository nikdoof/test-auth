from datetime import datetime, timedelta

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView, FormView, CreateView, ListView
from django.views.generic.detail import BaseDetailView
from django.conf import settings

from gargoyle import gargoyle

from utils import installed, blacklist_values, check_permissions, send_message
from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerCharacter
from sso.tasks import update_user_access
from hr.forms import RecommendationForm, ApplicationForm, NoteForm, BlacklistUserForm, AdminNoteForm
from hr.models import Recommendation, Application, Audit, Blacklist, BlacklistSource
from hr.app_defines import *

### General Views

class HrIndexView(TemplateView):
    """
    Gives the main HR index page, with various options displayed depending on their
    access level.
    """

    template_name = 'hr/index.html'

    def get_context_data(self, **kwargs):
        context = super(HrIndexView, self).get_context_data(**kwargs)
        context['hrstaff'] = check_permissions(self.request.user)
        context['can_recommend'] = len(blacklist_values(self.request.user, BLACKLIST_LEVEL_ADVISORY)) == 0
        return context

### Application Management

class HrViewUserApplications(TemplateView):
    """
    Shows a list of the user's applications in the system
    """

    template_name = 'hr/applications/view_list.html'

    def get_context_data(self, **kwargs):
        context = super(HrViewUserApplications, self).get_context_data(**kwargs)
        context['applications'] = Application.objects.filter(user=self.request.user).order_by('id')
        return context


class HrViewApplication(DetailView):
    """
    View a individual application and related details
    """

    template_name = 'hr/applications/view.html'
    context_object_name = "app"
    model = Application
    slug_field = 'id'

    def get_context_data(self, **kwargs):
        context = super(HrViewApplication, self).get_context_data(**kwargs)
        perm = check_permissions(self.request.user, self.object)
        if perm == HR_VIEWONLY:
            context['audit'] = self.object.audit_set.filter(event__in=[AUDIT_EVENT_STATUSCHANGE, AUDIT_EVENT_REJECTION, AUDIT_EVENT_ACCEPTED, AUDIT_EVENT_MESSAGE])
        elif perm == HR_ADMIN:
            context['hrstaff'] = True
            context['audit'] = self.object.audit_set.all()
        return context


class HrAddApplication(FormView):

    form_class = ApplicationForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(HrAddApplication, self).get_form_kwargs(**kwargs)
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        app = Application(user=self.request.user, character=form.cleaned_data['character'], corporation=form.cleaned_data['corporation'])
        app.save()
        messages.add_message(self.request, messages.INFO, "Your application to %s has been created." % app.corporation)
        return HttpResponseRedirect(reverse('hr-viewapplication', args=[app.id]))

    def get_template_names(self):
        if len(EVEPlayerCorporation.objects.filter(application_config__is_accepting=True)):
            return 'hr/applications/add.html'
        else:
            return 'hr/applications/noadd.html'

### Recommendation Management

class HrViewRecommendations(TemplateView):
    """
    Shows a list of the user's recommendations in the system
    """

    template_name = 'hr/recommendations/view_list.html'

    def get_context_data(self, **kwargs):
        context = super(HrViewRecommendations, self).get_context_data(**kwargs)
        context['recommendations'] = Recommendation.objects.filter(user=self.request.user)
        return context


class HrAddRecommendation(FormView):

    template_name = 'hr/recommendations/add.html'
    form_class = RecommendationForm

    def dispatch(self, request, *args, **kwargs):
        if len(blacklist_values(request.user, BLACKLIST_LEVEL_ADVISORY)):
            raise Http404
        return super(HrAddRecommendation, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        rec = Recommendation(user=self.request.user)
        rec.user_character = form.cleaned_data['character']
        rec.application = form.cleaned_data['application']
        rec.save()

        messages.add_message(self.request, messages.INFO, "Recommendation added to %s's application" % rec.application )
        return HttpResponseRedirect(reverse('hr-viewrecommendations'))

    def get_form_kwargs(self):
        kwargs = super(HrAddRecommendation, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class HrAdminApplications(ListView):

    model = Application
    template_name = 'hr/applications/admin/view_list.html'
    context_object_name = 'apps'

    def get_queryset(self):
        if self.request.user.has_perm('hr.can_view_all'):
            apps = Application.objects.all()
        elif self.request.user.has_perm('hr.can_view_corp'):
            apps = Application.objects.filter(corporation__id__in=set(EVEPlayerCharacter.objects.filter(eveaccount__user=self.request.user).values_list('corporation__id', flat=True)))
        else:
            apps = Application.objects.none()

        query = self.request.GET.get('q', None)
        order = self.request.GET.get('o', 'id')

        # Filter by the query string
        if query:
            apps = apps.filter(character__name__icontains=query)
        else:
            apps = apps.filter(status__in=[APPLICATION_STATUS_AWAITINGREVIEW, APPLICATION_STATUS_ACCEPTED, APPLICATION_STATUS_QUERY, APPLICATION_STATUS_FLAGGED])

        # If a invalid order as been passed, correct it
        if not order in ['id', 'corporation__name', 'character__name']:
            order = 'id'

        # If we've got a short search string, only get the first 50
        if query and len(query) < 3:
            apps = apps[:50]

        return apps.order_by(order)


class HrUpdateApplication(BaseDetailView):
    """
    Updates the status of a application if the workflow and permissions allow so.
    """
    model = Application
    slug_field = 'id'

    def render_to_response(self, context):
        status = self.kwargs.get('status', None)
        if status and int(status) in APPLICATION_STATUS_ROUTES[self.object.status]:
            perm = check_permissions(self.request.user, self.object)
            if perm == HR_ADMIN or (perm == HR_VIEWONLY and int(status) <= 1):
                if not self.object.status == status:
                    self.object.status = status
                    self.object.save(user=self.request.user)
                    self.object = self.model.objects.get(pk=self.object.pk)
                    messages.add_message(self.request, messages.INFO, "Application %s has been changed to %s" % (self.object.id, self.object.get_status_display()))
        else:
             messages.add_message(self.request, messages.ERROR, "Invalid status change request")
        return HttpResponseRedirect(reverse('hr-viewapplication', args=[self.object.id]))


class HrAddNote(CreateView):
    """
    View to add a note to a application
    """

    template_name = 'hr/applications/add_note.html'
    form_class = NoteForm
    model = Audit

    def dispatch(self, request, *args, **kwargs):
        if not check_permissions(request.user) == HR_ADMIN:
            return HttpResponseRedirect(reverse('hr-index'))
        self.application = Application.objects.get(pk=kwargs.get('applicationid'))
        return super(HrAddNote, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if check_permissions(self.request.user, self.application) == HR_ADMIN:
            self.object = form.save(commit=False)
            self.object.event = AUDIT_EVENT_NOTE
            self.object.application = self.application
            self.object.user = self.request.user
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('hr-viewapplication', args=[self.application.id])

    def get_context_data(self, **kwargs):
        context = super(HrAddNote, self).get_context_data(**kwargs)
        context['application'] = self.application
        return context


class HrAddMessage(HrAddNote):

    template_name = 'hr/applications/add_message.html'

    def dispatch(self, request, *args, **kwargs):
        self.application = Application.objects.get(pk=kwargs.get('applicationid'))
        self.perm = check_permissions(request.user, self.application)
        if not self.perm:
            return HttpResponseRedirect(reverse('hr-index'))
        return super(HrAddMessage, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        if self.perm == HR_ADMIN:
            return AdminNoteForm
        else:
            return NoteForm

    def get_form_kwargs(self):
        kwargs = super(HrAddMessage, self).get_form_kwargs()
        if self.perm == HR_ADMIN:
            kwargs['application'] = self.application
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.application = self.application
        self.object.event = AUDIT_EVENT_MESSAGE
        self.object.user = self.request.user
        self.object.save()
        if not self.application.user == self.request.user:
            try:
                send_message(self.application, 'message', note=self.object.text)
            except:
                pass
        return HttpResponseRedirect(self.get_success_url())

class HrRejectApplication(CreateView):

    template_name = 'hr/applications/reject.html'
    message_template_name = 'rejected'
    form_class = AdminNoteForm
    model = Audit
    application_change_status = APPLICATION_STATUS_REJECTED
    audit_event_type = AUDIT_EVENT_REJECTION

    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(Application, pk=kwargs.get('applicationid'))
        if not (check_permissions(request.user) == HR_ADMIN and request.user.has_perm('hr.can_accept')):
            return HttpResponseRedirect(reverse('hr-index'))
        return super(HrRejectApplication, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(HrRejectApplication, self).get_form_kwargs()
        kwargs['application'] = self.application
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(HrRejectApplication, self).get_context_data(**kwargs)
        context['application'] = self.application
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.application = self.application
        self.object.user = self.request.user
        self.object.event = self.audit_event_type
        self.object.save()

        self.object.application.status = self.application_change_status
        self.object.application.save(user=self.request.user)

        try:
            send_message(self.object.application, self.message_template_name, note=self.object.text)
        except:
            pass
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('hr-viewapplication', args=[self.application.id])


class HrAcceptApplication(HrRejectApplication):

    template_name = 'hr/applications/accept.html'
    message_template_name = 'accepted'
    application_change_status = APPLICATION_STATUS_ACCEPTED
    audit_event_type = AUDIT_EVENT_ACCEPTED

    def dispatch(self, request, *args, **kwargs):
        app = get_object_or_404(Application, pk=kwargs.get('applicationid'))
        if app.blacklisted:
            messages.add_message(request, messages.INFO, "This application has one or more blacklist entries and cannot be accepted.")
            return HttpResponseRedirect(reverse('hr-viewapplication', args=[app.id]))
        return super(HrAcceptApplication, self).dispatch(request, *args, **kwargs)


class HrBlacklistUser(FormView):

    template_name = 'hr/blacklist/blacklist.html'
    form_class = BlacklistUserForm

    def dispatch(self, request, *args, **kwargs):
        self.blacklist_user = get_object_or_404(User, id=kwargs.get('userid'))
        return super(HrBlacklistUser, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HrBlacklistUser, self).get_context_data(**kwargs)
        context['blacklistuser'] = self.blacklist_user
        return context

    def blacklist_item(self, type, value):
        Blacklist(type=type, value=value, level=self.level, source=self.source, expiry_date=self.expiry, created_by=self.request.user, reason=self.reason).save()

    def form_valid(self, form):
        self.source = BlacklistSource.objects.get(id=1)
        self.expiry = form.cleaned_data.get('expiry_date', None)
        if not self.expiry:
            self.expiry = datetime.utcnow() + timedelta(days=50*365) # 50 year default
        self.level = form.cleaned_data.get('level', 0)
        self.reason = form.cleaned_data.get('reason', 'No reason provided')

        # Blacklist email address
        self.blacklist_item(BLACKLIST_TYPE_EMAIL, self.blacklist_user.email)

        # Blacklist API keys
        for account in self.blacklist_user.eveaccount_set.all():
            self.blacklist_item(BLACKLIST_TYPE_APIUSERID, account.api_user_id)

        # Blacklist Characters
        for character in EVEPlayerCharacter.objects.filter(eveaccount__user=self.blacklist_user).distinct():
            self.blacklist_item(BLACKLIST_TYPE_CHARACTER, character.name)

        # Blacklist Reddit accounts
        if installed('reddit'):
            for account in self.blacklist_user.redditaccount_set.all():
                self.blacklist_item(BLACKLIST_TYPE_REDDIT, account.username)

        messages.add_message(self.request, messages.INFO, "User %s has been blacklisted" % self.blacklist_user.username )

        # Disable the account if requested
        if form.cleaned_data.get('disable', None):
            self.blacklist_user.active = False
            self.blacklist_user.save()
            messages.add_message(self.request, messages.INFO, "User %s disabled" % self.blacklist_user.username)

        update_user_access.delay(user=self.blacklist_user.id)

        return redirect('sso.views.user_view', username=self.blacklist_user.username)
