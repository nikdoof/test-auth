from datetime import datetime, timedelta
from django.utils import simplejson
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template.loader import render_to_string
from django.conf import settings

from utils import installed

from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerCharacter
from hr.forms import CreateRecommendationForm, CreateApplicationForm, NoteForm, BlacklistUserForm, AdminNoteForm
from hr.models import Recommendation, Application, Audit, Blacklist, BlacklistSource
from app_defines import *

### Shared Functions

def send_message(application, message_type, note=None):
    from django.core.mail import send_mail
    subject = render_to_string('hr/emails/%s_subject.txt' % message_type, { 'app': application })
    subject = ''.join(subject.splitlines())
    message = render_to_string('hr/emails/%s.txt' % message_type, { 'app': application, 'note': note })
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [application.user.email])
    except:
        pass

    if installed('reddit') and len(application.user.redditaccount_set.all()) > 0:
            from reddit.tasks import send_reddit_message

            for account in application.user.redditaccount_set.all():
                send_reddit_message.delay(to=account.username, subject=subject, message=message)


def check_permissions(user, application=None):
    """ Check if the user has permissions to view or admin the application """

    corplist = EVEPlayerCharacter.objects.select_related('roles').filter(eveaccount__user=user)
    if not application:
        if user.has_perm('hr.can_view_all') or user.has_perm('hr.can_view_corp') or corplist.filter(roles__name='roleDirector').count():
            return HR_ADMIN
    else:
        if application.user == user:
            return HR_VIEWONLY
        if user.has_perm('hr.can_view_all'):
            return HR_ADMIN
        else:
            # Give admin access to directors of the corp
            if application.corporation.id in corplist.filter(roles__name='roleDirector').values_list('corporation__id', flat=True):
                return HR_ADMIN

            # Give access to none director HR people access
            if application.corporation.id in corplist.values_list('corporation__id', flat=True) and user.has_perm('hr.can_view_corp'):
                return HR_ADMIN

    return HR_NONE

### General Views

@login_required
def index(request):
    hrstaff = check_permissions(request.user)
    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))

### Application Management

@login_required
def view_applications(request):
    """ Shows a list of the user's applications """

    apps = Application.objects.filter(user=request.user).order_by('id')
    return render_to_response('hr/applications/view_list.html', locals(), context_instance=RequestContext(request))

@login_required
def view_application(request, applicationid):
    """ View a individual application """

    app = get_object_or_404(Application, id=applicationid)

    perm = check_permissions(request.user, app)
    if perm == HR_VIEWONLY:
        audit = app.audit_set.filter(event__in=[AUDIT_EVENT_STATUSCHANGE, AUDIT_EVENT_REJECTION, AUDIT_EVENT_ACCEPTED, AUDIT_EVENT_MESSAGE])
    elif perm == HR_ADMIN:
        hrstaff = True
        audit = app.audit_set.all()
    else:
        return HttpResponseRedirect(reverse('hr.views.index'))

    # Respond to Reddit Comment Load
    # TODO: Move to reddit app?
    if installed('reddit') and request.GET.has_key('redditxhr') and request.is_ajax():
        posts = []
        for acc in app.user.redditaccount_set.all():
            try:
                accposts = acc.recent_posts()
            except:
                accposts = []
            posts.extend(accposts)
        return HttpResponse(simplejson.dumps(accposts), mimetype='application/javascript')

    return render_to_response('hr/applications/view.html', locals(), context_instance=RequestContext(request))

@login_required
def add_application(request):
    """ Create a new application to a corporation """

    clsform = CreateApplicationForm(request.user)
    if request.method == 'POST': 
        form = clsform(request.POST) 
        if form.is_valid():
            app = Application(user=request.user, character=form.cleaned_data['character'], corporation=form.cleaned_data['corporation'])
            app.save()
            messages.add_message(request, messages.INFO, "Your application to %s has been created." % app.corporation)
            return HttpResponseRedirect(reverse('hr.views.view_application', args=[app.id]))
    else:
        form = clsform() # An unbound form

    if len(EVEPlayerCorporation.objects.filter(application_config__is_accepting=True)):
        return render_to_response('hr/applications/add.html', locals(), context_instance=RequestContext(request))
    else:
        return render_to_response('hr/applications/noadd.html', locals(), context_instance=RequestContext(request)) 

### Recommendation Management

@login_required
def view_recommendations(request):
    """ View a list of recommendations the user has made """

    recs = Recommendation.objects.filter(user=request.user)
    return render_to_response('hr/recommendations/view_list.html', locals(), context_instance=RequestContext(request))

@login_required
def add_recommendation(request):

    clsform = CreateRecommendationForm(request.user)
    if request.method == 'POST': 
        form = clsform(request.POST) 
        if form.is_valid():
            rec = Recommendation(user=request.user)
            rec.user_character = form.cleaned_data['character']
            rec.application = form.cleaned_data['application']
            rec.save()

            messages.add_message(request, messages.INFO, "Recommendation added to %s's application" % rec.application )
            return HttpResponseRedirect(reverse('hr.views.view_recommendations'))
            
    else:
        form = clsform() # An unbound form

    return render_to_response('hr/recommendations/add.html', locals(), context_instance=RequestContext(request))

@login_required
def admin_applications(request):
    # Get the list of viewable applications by the admin
    corplist = EVEPlayerCharacter.objects.filter(eveaccount__user=request.user).values_list('corporation', flat=True)
    view_status = [APPLICATION_STATUS_AWAITINGREVIEW, APPLICATION_STATUS_ACCEPTED, APPLICATION_STATUS_QUERY, APPLICATION_STATUS_FLAGGED]

    if request.user.has_perm('hr.can_view_all'):
        apps = Application.objects.all()
    elif request.user.has_perm('hr.can_view_corp'):
        apps = Application.objects.filter(corporation__id__in=list(corplist))
    else:
        return HttpResponseRedirect(reverse('hr.views.index'))

    if 'q' in request.GET:
        query = request.GET['q']
        apps = apps.filter(character__name__icontains=query)
    else:
        apps = apps.filter(status__in=view_status)

    if 'o' in request.GET:
        order = request.GET['o']
        if order in ['id', 'corporation__name', 'character__name']:
            apps = apps.order_by(order)

    if 'l' in request.GET:
        limit = request.GET['l']
        apps = apps[:limit]

    return render_to_response('hr/applications/admin/view_list.html', locals(), context_instance=RequestContext(request))

@login_required
def update_application(request, applicationid, status): 
    """ Update a application's status """

    app = get_object_or_404(Application, id=applicationid)

    if int(status) in APPLICATION_STATUS_ROUTES[app.status]:
        perm = check_permissions(request.user, app)
        if perm == HR_ADMIN or (perm == HR_VIEWONLY and int(status) <= 1):
            if not app.status == status:
                app.status = status
                app.save(user=request.user)
    else:
         messages.add_message(request, messages.ERROR, "Invalid status change request")
    return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))

@login_required
def add_note(request, applicationid):
    """ Add a note to a application """

    if check_permissions(request.user) == HR_ADMIN:
        if request.method == 'POST':
            app = Application.objects.get(id=applicationid)
            if check_permissions(request.user, app) == HR_ADMIN:
                obj = Audit(application=app, user=request.user, event=AUDIT_EVENT_NOTE)
                form = NoteForm(request.POST, instance=obj)
                if form.is_valid():
                    obj = form.save()
                    return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))

        form = NoteForm()
        return render_to_response('hr/applications/add_note.html', locals(), context_instance=RequestContext(request))

    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))


@login_required
def add_message(request, applicationid):
    """ Send a message to the end user and note it on the application """

    app = Application.objects.get(id=applicationid)
    perm = check_permissions(request.user, app)
    if perm:
        if request.method == 'POST':
            obj = Audit(application=app, user=request.user, event=AUDIT_EVENT_MESSAGE)
            if perm == HR_ADMIN:
                form = AdminNoteForm(request.POST, instance=obj, application=app)
            else:
                form = NoteForm(request.POST, instance=obj)
            if form.is_valid():
                obj = form.save()
                if not app.user == request.user:
                    send_message(obj.application, 'message', note=obj.text)
                return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))

        if perm == HR_ADMIN:
            form = AdminNoteForm(application=app)
        else:
            form = NoteForm()
        return render_to_response('hr/applications/add_message.html', locals(), context_instance=RequestContext(request))

    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))

@login_required
def reject_application(request, applicationid):
    """ Reject the application and notify the user """

    if check_permissions(request.user) == HR_ADMIN and request.user.has_perm('hr.can_accept'):
        app = Application.objects.get(id=applicationid)
        if request.method == 'POST':
            if check_permissions(request.user, app) == HR_ADMIN:
                obj = Audit(application=app, user=request.user, event=AUDIT_EVENT_REJECTION)
                form = AdminNoteForm(request.POST, instance=obj, application=app)
                if form.is_valid():
                    obj = form.save()
                    obj.application.status = APPLICATION_STATUS_REJECTED
                    obj.application.save(user=request.user)
                    send_message(obj.application, 'rejected', note=obj.text)
                    return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))

        form = AdminNoteForm(application=app)
        return render_to_response('hr/applications/reject.html', locals(), context_instance=RequestContext(request))

    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))

@login_required
def accept_application(request, applicationid):
    """ Accept the application and notify the user """

    if check_permissions(request.user) == HR_ADMIN and request.user.has_perm('hr.can_accept'):
        app = Application.objects.get(id=applicationid)

        if app.blacklisted:
            messages.add_message(request, messages.INFO, "This application has one or more blacklist entries and cannot be accepted.")
            return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))

        if request.method == 'POST':
            if check_permissions(request.user, app) == HR_ADMIN:
                obj = Audit(application=app, user=request.user, event=AUDIT_EVENT_ACCEPTED)
                form = AdminNoteForm(request.POST, instance=obj, application=app)
                if form.is_valid():
                    obj = form.save()
                    obj.application.status = APPLICATION_STATUS_ACCEPTED
                    obj.application.save(user=request.user)
                    send_message(obj.application, 'accepted', note=obj.text)
            return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))

        form = AdminNoteForm(application=app)
        return render_to_response('hr/applications/accept.html', locals(), context_instance=RequestContext(request))

    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))


def blacklist_user(request, userid):

    if request.user.has_perm('hr.add_blacklist'):

        u = get_object_or_404(User, id=userid)

        if request.method == 'POST':
            form = BlacklistUserForm(request.POST)
            if form.is_valid():
                source = BlacklistSource.objects.get(id=1)

                if not form.cleaned_data.get('expiry_date', None):
                    expiry = datetime.utcnow() + timedelta(days=50*365)
                else:
                    expiry = form.cleaned_data['expiry_date']

                level = form.cleaned_data.get('level', 0)
                print level

                def blacklist_item(type, value):
                    o = Blacklist(type=type, value=value, level=level, source=source, expiry_date=expiry, created_by=request.user, reason=form.cleaned_data['reason'])
                    o.save()

                for ea in u.eveaccount_set.all():
                    blacklist_item(BLACKLIST_TYPE_APIUSERID, ea.api_user_id)

                for ra in u.redditaccount_set.all():
                    blacklist_item(BLACKLIST_TYPE_REDDIT, ra.username)

                for char in EVEPlayerCharacter.objects.filter(eveaccount__user=u):
                    blacklist_item(BLACKLIST_TYPE_CHARACTER, char.name)

                blacklist_item(BLACKLIST_TYPE_EMAIL, u.email)

                messages.add_message(request, messages.INFO, "User %s has been blacklisted" % u.username )

                if form.cleaned_data.get('disable', None):
                    # Disable the account
                    u.active = False
                    u.save()

                    for acc in u.serviceaccount_set.all():
                        acc.delete()

                    messages.add_message(request, messages.INFO, "User %s disabled" % u.username )

                return redirect('sso.views.user_view', username=u.username)
            else:
                messages.add_message(request, messages.ERROR, "Error while processing the form")

        form = BlacklistUserForm()
        return render_to_response('hr/blacklist/blacklist.html', locals(), context_instance=RequestContext(request))

    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))

