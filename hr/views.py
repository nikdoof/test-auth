import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from hr.forms import CreateRecommendationForm, CreateApplicationForm
from hr.models import Recommendation, Application


def index(request):
    if request.user.is_staff or 'hrstaff' in request.user.groups.all():
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

            request.user.message_set.create(message="Application has been submitted." % rec.application )
            return HttpResponseRedirect(reverse('hr.views.view_applications'))
        else:
            return HttpResponseRedirect(reverse('hr.views.add_application'))
            
    else:
        form = clsform() # An unbound form

    return render_to_response('hr/applications/add.html', locals(), context_instance=RequestContext(request))

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
            return HttpResponseRedirect(reverse('hr.views.add_recommendation'))
            
    else:
        form = clsform() # An unbound form

    return render_to_response('hr/recommendations/add.html', locals(), context_instance=RequestContext(request))



