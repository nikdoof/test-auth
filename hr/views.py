import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template.loader import render_to_string

import settings

from eve_api.models import EVEAccount, EVEPlayerCorporation
from reddit.models import RedditAccount

from hr.forms import CreateRecommendationForm, CreateApplicationForm, CreateApplicationStatusForm
from hr.models import Recommendation, Application

from app_defines import *

def index(request):
    if request.user.is_staff or Group.objects.get(name=settings.HR_STAFF_GROUP) in request.user.groups.all():
        hrstaff = True

    return render_to_response('hr/index.html', locals(), context_instance=RequestContext(request))

### Application Management

@login_required
def view_applications(request):
    apps = Application.objects.filter(user=request.user)
    return render_to_response('hr/applications/view_list.html', locals(), context_instance=RequestContext(request))

@login_required
def view_application(request, applicationid):
    try:
        app = Application.objects.get(id=applicationid)
    except Application.DoesNotExist:
        return HttpResponseRedirect(reverse('hr.views.index'))

    if not app.user == request.user and not (request.user.is_staff or Group.objects.get(name=settings.HR_STAFF_GROUP) in request.user.groups.all()):
        return HttpResponseRedirect(reverse('hr.views.index'))

    if request.user.is_staff or Group.objects.get(name=settings.HR_STAFF_GROUP) in request.user.groups.all():
        hrstaff = True
    else:
        hrstaff = False

    if hrstaff or app.status < 1:
        appform = CreateApplicationStatusForm(hrstaff)
        form = appform(initial={'application': app.id, 'new_status': app.status})

    eveacc = EVEAccount.objects.filter(user=app.user)
    redditacc = RedditAccount.objects.filter(user=app.user)
    recs = Recommendation.objects.filter(application=app)

    posts = []
    for acc in redditacc:
        posts.extend(acc.recent_posts())

    return render_to_response('hr/applications/view.html', locals(), context_instance=RequestContext(request))

@login_required
def add_application(request):

    clsform = CreateApplicationForm(request.user)
    if request.method == 'POST': 
        form = clsform(request.POST) 
        if form.is_valid():
            app = Application()

            app.user = request.user
            app.character = form.cleaned_data['character']
            app.corporation = form.cleaned_data['corporation']
            app.save()

            request.user.message_set.create(message="Your application to %s has been created." % app.corporation)
            return HttpResponseRedirect(reverse('hr.views.view_applications'))
            
    else:
        form = clsform() # An unbound form

    if len(EVEPlayerCorporation.objects.filter(applications=True)):
        return render_to_response('hr/applications/add.html', locals(), context_instance=RequestContext(request))
    else:
        return render_to_response('hr/applications/noadd.html', locals(), context_instance=RequestContext(request)) 

### Recommendation Management

@login_required
def view_recommendations(request):
    recs = Recommendation.objects.filter(user=request.user, application__status=0)
    return render_to_response('hr/recommendations/view_list.html', locals(), context_instance=RequestContext(request))

@login_required
def view_recommendation(request, recommendationid):
    try:
        rec = Recommendation.objects.get(id=recommendationid, user=request.user)
    except Recommendation.DoesNotExist:
        return HttpResponseRedirect(reverse('hr.views.index'))
    return render_to_response('hr/recommendations/view.html', locals(), context_instance=RequestContext(request))

@login_required
def add_recommendation(request):

    clsform = CreateRecommendationForm(request.user)

    if request.method == 'POST': 
        form = clsform(request.POST) 
        if form.is_valid():
            rec = Recommendation()

            rec.user = request.user
            rec.user_character = form.cleaned_data['character']
            rec.application = form.cleaned_data['application']
            rec.created_by = request.user
            rec.last_updated_by = request.user
            rec.save()

            request.user.message_set.create(message="Recommendation added to %s's application" % rec.application )
            return HttpResponseRedirect(reverse('hr.views.view_recommendations'))
            
    else:
        form = clsform() # An unbound form

    return render_to_response('hr/recommendations/add.html', locals(), context_instance=RequestContext(request))

@login_required
def admin_applications(request):
    if not (request.user.is_staff or Group.objects.get(name=settings.HR_STAFF_GROUP) in request.user.groups.all()):
        return HttpResponseRedirect(reverse('hr.views.index'))

    view_status = [APPLICATION_STATUS_AWAITINGREVIEW, APPLICATION_STATUS_ACCEPTED, APPLICATION_STATUS_QUERY]
    apps = Application.objects.filter(status__in=view_status)
    return render_to_response('hr/applications/admin/view_list.html', locals(), context_instance=RequestContext(request))

@login_required
def update_application(request, applicationid):   
    if request.method == 'POST':
        appform = CreateApplicationStatusForm(True)
        form = appform(request.POST)
        if form.is_valid():
            app = Application.objects.get(id=form.cleaned_data['application'])

            hrstaff = (request.user.is_staff or Group.objects.get(name=settings.HR_STAFF_GROUP) in request.user.groups.all())
            if not hrstaff and int(form.cleaned_data['new_status']) > 1:
                return HttpResponseRedirect(reverse('hr.views.index'))

            if not app.status == form.cleaned_data['new_status']:
            
                app.status = form.cleaned_data['new_status']
                app.save()

                def send_message(application, message_type):
                    from django.core.mail import send_mail
                    subject = render_to_string('hr/emails/%s_subject.txt' % message_type, { 'app': app })
                    subject = ''.join(subject.splitlines())
                    message = render_to_string('hr/emails/%s.txt' % message_type, { 'app': app })
                    #send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [application.user.email])

                    if len(application.user.redditaccount_set.all()) > 0:
                        from reddit.api import Inbox
                        ib = Inbox(settings.REDDIT_USER, settings.REDDIT_PASSWD)
                        ib.send(application.user.redditaccount_set.all()[0].username, subject, message)

                if int(app.status) == APPLICATION_STATUS_ACCEPTED:
                    send_message(app, 'accepted')
                elif int(app.status) == APPLICATION_STATUS_REJECTED:
                    send_message(app, 'rejected')

    return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))
