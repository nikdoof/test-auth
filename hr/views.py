import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

import settings

from eve_api.models import EVEAccount, EVEPlayerCorporation
from reddit.models import RedditAccount

from hr.forms import CreateRecommendationForm, CreateApplicationForm, CreateApplicationStatusForm
from hr.models import Recommendation, Application

from app_defines import *

def index(request):
    if request.user.is_staff or settings.HR_STAFF_GROUP in request.user.groups.all():
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

    if not app.user == request.user and not (request.user.is_staff or settings.HR_STAFF_GROUP in request.user.groups.all()):
        return HttpResponseRedirect(reverse('hr.views.index'))

    if request.user.is_staff or settings.HR_STAFF_GROUP in request.user.groups.all():
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
    if not (request.user.is_staff or settings.HR_STAFF_GROUP in request.user.groups.all()):
        return HttpResponseRedirect(reverse('hr.views.index'))

    apps = Application.objects.filter(status=APPLICATION_STATUS_AWAITINGREVIEW)
    return render_to_response('hr/applications/admin/view_list.html', locals(), context_instance=RequestContext(request))

@login_required
def update_application(request, applicationid):   
    if request.method == 'POST':
        appform = CreateApplicationStatusForm(True)
        form = appform(request.POST)
        if form.is_valid():
            app = Application.objects.get(id=form.cleaned_data['application'])

            hrstaff = (request.user.is_staff or settings.HR_STAFF_GROUP in request.user.groups.all())
            if not hrstaff and int(form.cleaned_data['new_status']) > 1:
                return HttpResponseRedirect(reverse('hr.views.index'))

            app.status = form.cleaned_data['new_status']
            app.save()

            if app.status == APPLICATION_STATUS_AWAITINGREVIEW:
                app.user.message_set.create(message="Your application for %s to %s has been submitted." % (app.character, app.corporation))
            if app.status == APPLICATION_STATUS_ACCEPTED:
                app.user.message_set.create(message="Your application for %s to %s has been accepted." % (app.character, app.corporation))
            elif app.status == APPLICATION_STATUS_REJECTED:
                app.user.message_set.create(message="Your application for %s to %s has been rejected." % (app.character, app.corporation))

    return HttpResponseRedirect(reverse('hr.views.view_application', args=[applicationid]))
