from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse

from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required

from groups.app_defines import *
from groups.forms import GroupRequestForm

def index(request):
    return HttpResponseRedirect(reverse('groups.views.group_list'))

@login_required
def group_list(request):
    """ View all groups, for users only public ones """

    if request.user.is_superuser:
        groups = Group.objects.select_related('groupinformation').all()
    else:
        groups = Group.objects.select_related('groupinformation').filter(Q(groupinformation__public=True) | 
                                                                         Q(groupinformation__admins__in=[request.user]) | 
                                                                         Q(user__in=[request.user]))

    # Process the query into a list of tuples including status
    group_list = []
    for group in set(groups):
        if request.user in group.groupinformation.admins.all():
            status = "Admin"
        elif request.user in group.user_set.all():
            status = "Member"
        else:
            status = None

        if group.groupinformation.requestable and not group.groupinformation.type == GROUP_TYPE_MANAGED:
            requestable = True
        else:
            requestable = False

        group_list.append((group.id, group.name, status, requestable))

    return render_to_response('groups/group_list.html', locals(), context_instance=RequestContext(request))

@login_required
def view_group(request):
    pass

@login_required
def create_request(request, groupid):

    group = get_object_or_404(Group, id=groupid)

    if not group.groupinformation.requestable and not request.user in group.user_set.all():
        return HttpResponseRedirect(reverse('groups.views.index'))

    if request.method == 'POST':
        form = GroupRequestForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.group = group
            obj.changed_by = request.user
            obj.save()
            messages.add_message(request, messages.INFO, "You membership request has been created.")
            return HttpResponseRedirect(reverse('groups.views.index')) # Redirect after POST
    else:
        form = GroupRequestForm() # An unbound form

    return render_to_response('groups/create_request.html', locals(), context_instance=RequestContext(request))    
