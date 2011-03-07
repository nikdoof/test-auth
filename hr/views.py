import datetime
import simplejson
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template.loader import render_to_string
from django.conf import settings

from utils import installed

from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerCharacter
from hr.forms import CreateRecommendationForm, CreateApplicationForm, NoteForm
from hr.models import Recommendation, Application, Audit
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
            send_reddit_message.delay(to=application.user.redditaccount_set.all()[0].username, subject=subject, message=message)


def check_permissions(user, application=None):
    """ Check if the user has permissions to view or admin the application """

    corplist = EVEPlayerCharacter.objects.filter(eveaccount__user=user,corporation__applications=True)
    if not application:
        if user.has_perm('hr.can_view_all') or user.has_perm('hr.can_view_corp') or corplist.filter(director=True).count():
            return HR_ADMIN
    else:
        if application.user == user:
            return HR_VIEWONLY
        if user.has_perm('hr.can_view_all'):
            return HR_ADMIN
        else:
            # Give admin access to directors of the corp
            if application.corporation.id in corplist.filter(director=True).values_list('corporation__id', flat=True):
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

            if form.cleaned_data['character'].corporation == form.cleaned_data['corporation']:
                messages.add_message(request, messages.WARNING, "This character is already a member of %s" % form.cleaned_data['corporation'])
                return HttpResponseRedirect(reverse('hr.views.view_applications'))

            app = Application(user=request.user, character=form.cleaned_data['character'], corporation=form.cleaned_data['corporation'])
            app.save()

            messages.add_message(request, messages.INFO, "Your application to %s has been created." % app.corporation)
            return HttpResponseRedirect(reverse('hr.views.view_application', args=[app.id]))
            
    else:
        form = clsform() # An unbound form

    if len(EVEPlayerCorporation.objects.filter(applications=True)):
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
        if order in ['id', 'corporation', 'character']:
            apps = apps.order_by(order)

    if 'l' in request.GET:
        limit = request.GET['l']
        apps = apps[:limit]

    return render_to_response('hr/applications/admin/view_list.html', locals(), context_instance=RequestContext(request))

@login_required
def update_application(request, applicationid, status): 
    """ Update a application's status """

    app = get_object_or_404(Application, id=applicationid)
    if check_permissions(request.user, app):
        if not app.status == status:
            app.status = status
            app.save(user=request.user)
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

    app = get_object_or_404(Application, id=applicationid)
    if check_permissions(request.user, app):
        if request.method == 'POST':
            obj = Audit(application=app, user=request.user, event=AUDIT_EVENT_MESSAGE)
            form = NoteForm(request.POST, instance=obj)
            if form.is_valid():
                obj = form.save()
                if not app.user == request.user:
                    send_message(obj.application, 'message', note=obj.text)
                return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))

        form = NoteForm()
        return render_to_response('hr/applications/add_message.html', locals(), context_instance=RequestContext(request))

    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))

@login_required
def reject_application(request, applicationid):
    """ Reject the application and notify the user """

    if check_permissions(request.user) == HR_ADMIN and request.user.has_perm('hr.can_accept'):
        if request.method == 'POST':
            app = Application.objects.get(id=applicationid)
            if check_permissions(request.user, app) == HR_ADMIN:
                obj = Audit(application=app, user=request.user, event=AUDIT_EVENT_REJECTION)
                form = NoteForm(request.POST, instance=obj)
                if form.is_valid():
                    obj = form.save()
                    obj.application.status = APPLICATION_STATUS_REJECTED
                    obj.application.save(user=request.user)
                    send_message(obj.application, 'rejected', note=obj.text)
                    return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))

        form = NoteForm()
        return render_to_response('hr/applications/reject.html', locals(), context_instance=RequestContext(request))

    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))

@login_required
def accept_application(request, applicationid):
    """ Accept the application and notify the user """

    if check_permissions(request.user) == HR_ADMIN and request.user.has_perm('hr.can_accept'):
        if request.method == 'POST':
            app = Application.objects.get(id=applicationid)
            if check_permissions(request.user, app) == HR_ADMIN:
                obj = Audit(application=app, user=request.user, event=AUDIT_EVENT_ACCEPTED)
                form = NoteForm(request.POST, instance=obj)
                if form.is_valid():
                    obj = form.save()
                    obj.application.status = APPLICATION_STATUS_ACCEPTED
                    obj.application.save(user=request.user)
                    send_message(obj.application, 'accepted', note=obj.text)
                    return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))

        form = NoteForm()
        return render_to_response('hr/applications/accept.html', locals(), context_instance=RequestContext(request))

    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))
