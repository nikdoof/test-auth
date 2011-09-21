from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse

from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required

from groups.models import GroupInformation, GroupRequest
from groups.app_defines import *
from groups.forms import GroupRequestForm

from sso.tasks import update_user_access


@login_required
def group_list(request):
    """ View all groups, for users only public ones """

    if request.user.is_superuser:
        groups = Group.objects.select_related('groupinformation').all()
    else:
        groups = Group.objects.select_related('groupinformation').filter(Q( Q(groupinformation__public=True) | Q(groupinformation__requestable=True) ) |
                                                                         Q(groupinformation__admins__in=[request.user]) |
                                                                         Q(user__in=[request.user]))

    # Process the query into a list of tuples including status
    group_list = []
    for group in set(groups):

        if not group.groupinformation:
            g, c = GroupInformation.objects.get_or_create(group=group)

        if group.groupinformation and request.user in group.groupinformation.admins.all():
            status = "Admin"
        elif request.user in group.user_set.all():
            status = "Member"
        else:
            status = None

        requestable = False
        if group.groupinformation and group.groupinformation.requestable:
            if group.groupinformation.parent:
                if group.groupinformation.parent in request.user.groups.all():
                    requestable = True
            else:
                requestable = True

        if not status and not group.groupinformation.public and not requestable:
            continue

        fixed = not group.groupinformation.type == GROUP_TYPE_PERMISSION
	pending = group.requests.filter(status=REQUEST_PENDING,user=request.user).count()

        group_list.append((group.id, group.name, group.groupinformation.description, status, requestable, fixed, pending, group.groupinformation.moderated))

    group_list = sorted(group_list, key=lambda name: name[1].lower())

    return render_to_response('groups/group_list.html', locals(), context_instance=RequestContext(request))


@login_required
def create_request(request, groupid):

    group = get_object_or_404(Group, id=groupid)

    if request.user in group.user_set.all() or not group.groupinformation.requestable:
        return HttpResponseRedirect(reverse('groups.views.group_list'))

    if group.groupinformation.parent and not group.groupinformation.parent in request.user.groups.all():
       return HttpResponseRedirect(reverse('groups.views.group_list'))

    if group.requests.filter(status=REQUEST_PENDING,user=request.user).count():
        messages.add_message(request, messages.INFO, "You already have a pending request for %s" % group.name)
        return HttpResponseRedirect(reverse('groups.views.group_list'))

    if not group.groupinformation.moderated:
        # Unmoderated group, so accept the application
        request.user.groups.add(group)
        update_user_access.delay(request.user.id)
        messages.add_message(request, messages.INFO, "You are now a member of %s" % (group))
        return HttpResponseRedirect(reverse('groups.views.group_list'))

    if request.method == 'POST':
        form = GroupRequestForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.group = group
            obj.changed_by = request.user
            obj.save()
            messages.add_message(request, messages.INFO, "You membership request has been created.")
            return HttpResponseRedirect(reverse('groups.views.group_list')) # Redirect after POST
    else:
        form = GroupRequestForm() # An unbound form

    return render_to_response('groups/create_request.html', locals(), context_instance=RequestContext(request))


@login_required
def accept_request(request, requestid):

    requestobj = get_object_or_404(GroupRequest, id=requestid)

    if request.user in requestobj.group.groupinformation.admins.all() or request.user.is_superuser:
        requestobj.status = REQUEST_ACCEPTED
        requestobj.user.groups.add(requestobj.group)
        requestobj.changed_by = request.user
        requestobj.save()
        update_user_access.delay(requestobj.user.id)
        messages.add_message(request, messages.INFO, "%s has been accepted into %s" % (requestobj.user, requestobj.group))
    return HttpResponseRedirect(reverse('groups.views.admin_group', args=[requestobj.group.id]))


@login_required
def reject_request(request, requestid):

    requestobj = get_object_or_404(GroupRequest, id=requestid)
    if request.user in requestobj.group.groupinformation.admins.all() or request.user.is_superuser:
        requestobj.status = REQUEST_REJECTED
        requestobj.changed_by = request.user
        requestobj.save()
        messages.add_message(request, messages.INFO, "%s has been rejected for %s" % (requestobj.user, requestobj.group))
    return HttpResponseRedirect(reverse('groups.views.admin_group', args=[requestobj.group.id]))


@login_required
def admin_group(request, groupid):

    group = get_object_or_404(Group, id=groupid)
    if group.groupinformation and request.user in group.groupinformation.admins.all() or request.user.is_superuser:

        member_list = []
        for member in set(group.user_set.all()):
            if group.groupinformation and member in group.groupinformation.admins.all():
                status = "Admin"
            else:
                status = "Member"

            char = member.get_profile().primary_character
            if char:
                charname = "[%s] %s" % (char.corporation.ticker, char.name)
            else:
                charname = "Unknown"

            member_list.append((member, charname, status))

        requests = group.requests.filter(status=REQUEST_PENDING)
        return render_to_response('groups/group_admin.html', locals(), context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('groups.views.group_list'))


@login_required
def promote_member(request, groupid, userid):

    if request.user.is_superuser:

        user = get_object_or_404(User, id=userid)
        group = get_object_or_404(Group, id=groupid)

        if not user in group.groupinformation.admins.all():
            group.groupinformation.admins.add(user)
            messages.add_message(request, messages.INFO, "%s is now a admin of %s" % (user.username, group.name))
        else:
            group.groupinformation.admins.remove(user)
            messages.add_message(request, messages.INFO, "%s is no longer a admin of %s" % (user.username, group.name))

    return HttpResponseRedirect(reverse('groups.views.admin_group', args=[groupid]))


@login_required
def kick_member(request, groupid, userid):

    group = get_object_or_404(Group, id=groupid)
    user = get_object_or_404(User, id=userid)

    if not group.groupinformation.type in [GROUP_TYPE_MANAGED]:
        if user == request.user:
            if user in group.groupinformation.admins.all():
                group.groupinformation.admins.remove(user)
            user.groups.remove(group)
            update_user_access.delay(user.id)
            messages.add_message(request, messages.INFO, "You have left the group %s" % group.name)

        elif request.user in group.groupinformation.admins.all() or request.user.is_superuser:
            if not user in group.groupinformation.admins.all():
                user.groups.remove(group)
                update_user_access.delay(user.id)
                messages.add_message(request, messages.INFO, "%s has been removed from %s." % (user.username, group.name))
            else:
                messages.add_message(request, messages.INFO, "%s is a admin of %s and cannot be removed." % (user.username, group.name))

            return HttpResponseRedirect(reverse('groups.views.admin_group', args=[groupid]))

    return HttpResponseRedirect(reverse('groups.views.group_list'))
