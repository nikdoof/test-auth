import celery

from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import Http404
from django.core import serializers

from eve_proxy.models import ApiAccessLog
from eve_proxy.exceptions import DocumentRetrievalError
from eve_api.forms import EveAPIForm
from eve_api.models import EVEAccount, EVEPlayerCharacter, EVEPlayerCorporation
from eve_api.tasks import import_apikey_result


@login_required
def eveapi_add(request, post_save_redirect='/'):
    """ Add a EVE API key to a user's account """

    if request.method == 'POST':
        form = EveAPIForm(request.POST)
        if form.is_valid():

            acc = form.save()
            print acc
            task = import_apikey_result.delay(api_key=acc.api_key, api_userid=acc.api_user_id, user=request.user.id)
            try:
                task.wait(10)
            except celery.exceptions.TimeoutError:
                msg = "The addition of your API key is still processing, please check back in a minute or so."
            except DocumentRetrievalError:
                msg = "An issue with the EVE API was encountered while adding your API, please try again later."
            except:
                msg = "An unknown error was encountered while trying to add your API key, please try again later."
            else:
                msg = "EVE API key %d successfully added." % form.cleaned_data['api_user_id']
            messages.success(request, msg, fail_silently=True)
            return redirect(post_save_redirect)
    else:
        form = EveAPIForm(initial={'user': request.user.id }) # An unbound form

    return render_to_response('eve_api/add.html', locals(), context_instance=RequestContext(request))


@login_required
def eveapi_update(request, userid, post_save_redirect='/'):
    """ Update a EVE API Key """

    acc = get_object_or_404(EVEAccount, pk=userid)
    if not acc.user == request.user and not request.user.is_staff:
        raise Http404    

    if request.method == 'POST':
        form = EveAPIForm(request.POST, instance=acc)
        if form.is_valid():
            if form.has_changed() and ('api_key' in form.changed_data):
                #acc = form.save()
                task = import_apikey_result.delay(api_key=acc.api_key, api_userid=acc.api_user_id, user=request.user.id)
                try:
                    task.wait(30)
                except celery.exceptions.TimeoutError:
                    msg = "The addition of your API key is still processing, please check back in a minute or so."
                except DocumentRetrievalError:
                    msg = "An issue with the EVE API was encountered while adding your API, please try again later."
                except:
                    msg = "An unknown error was encountered while trying to add your API key, please try again later."
                else:
                    msg = "EVE API key %d successfully updated." % acc.api_user_id
            else:
                if form.has_changed():
                    form.save()
                msg = "EVE API key %d successfully updated." % acc.api_user_id


            messages.success(request, msg, fail_silently=True)
            return redirect(post_save_redirect)
    else:
        form = EveAPIForm(instance=acc) # An unbound form

    return render_to_response('eve_api/update.html', locals(), context_instance=RequestContext(request))


@login_required
def eveapi_del(request, userid, post_save_redirect='/'):
    """ Delete a EVE API key from a account """

    try:
        acc = EVEAccount.objects.get(pk=userid)
    except EVEAccount.DoesNotExist:
        return redirect(post_save_redirect)
    if acc.user == request.user:
        acc.delete()
        messages.success(request, "EVE API key successfully deleted.", fail_silently=True)

    return redirect(post_save_redirect)


@login_required
def eveapi_refresh(request, userid, post_save_redirect='/'):
    """ Force refresh a EVE API key """

    try:
        acc = EVEAccount.objects.get(pk=userid)
    except EVEAccount.DoesNotExist:
        pass
    else:
        if acc.user == request.user or request.user.is_superuser:
            task = import_apikey_result.delay(api_key=acc.api_key, api_userid=acc.api_user_id, force_cache=True, user=request.user.id)
            if request.is_ajax():
                try:
                    acc = task.wait(30)
                except (celery.exceptions.TimeoutError, DocumentRetrievalError):
                    acc = EVEAccount.objects.get(pk=userid)
                if acc:
                    ret = [acc]
                else:
                    ret = []
                return HttpResponse(serializers.serialize('json', ret), mimetype='application/javascript')
            else:
                messages.add_message(request, messages.INFO, "Key %s has been queued to be refreshed from the API" % acc.api_user_id)

    return redirect(post_save_redirect)


@login_required
def eveapi_log(request, userid):
    """ Provides a list of access logs for a specific EVE API key """

    acc = get_object_or_404(EVEAccount, pk=userid)
    if acc and (acc.user == request.user or request.user.is_staff):
        logs = ApiAccessLog.objects.filter(userid=userid).order_by('-time_access')[:50]
        return render_to_response('eve_api/log.html', locals(), context_instance=RequestContext(request))


@login_required
def eveapi_character(request, charid=None):
    """ Provide a list of characters, or a indivdual character sheet """

    if charid:
        character = get_object_or_404(EVEPlayerCharacter.objects.select_related('corporation', 'corporation__aliance'), id=charid)

        #Check if the user has permission to see the character profile
        if not request.user.has_perm('eve_api.can_view_all_characters') and (not character.account or not request.user == character.account.user):
            raise Http404

        try:
            current_training = character.eveplayercharacterskill_set.get(in_training__gt=0)
        except:
            current_training = None
        skills = character.eveplayercharacterskill_set.all().order_by('skill__group__name', 'skill__name')

        skillTree = []
        currentSkillGroup = 0
        for skill in skills:
            if not skill.skill.group.id == currentSkillGroup:
                currentSkillGroup = skill.skill.group.id
                skillTree.append([0, skill.skill.group.name, []])
            
            skillTree[-1][0] += skill.skillpoints
            skillTree[-1][2].append(skill)

        return render_to_response('eve_api/character.html', locals(), context_instance=RequestContext(request))

    characters = EVEPlayerCharacter.objects.select_related('corporation', 'corporation__alliance').filter(eveaccount__user=request.user).only('id', 'name', 'corporation__name', 'corporation__alliance__name')
    return render_to_response('eve_api/character_list.html', locals(), context_instance=RequestContext(request))


@login_required
def eveapi_corporation(request, corporationid):
    """
    Provide details of a corporation, and for admins, a list of members
    """

    corporation = get_object_or_404(EVEPlayerCorporation, id=corporationid)
    if request.user.is_superuser:
        view_members = True

        memberdata = corporation.eveplayercharacter_set.all()
        if corporation.member_count:
            api_members = memberdata.filter(eveaccount__isnull=False).count()
            percentage = (float(api_members) / corporation.member_count) * 100
        members = memberdata.order_by('corporation_date').only('id', 'name', 'corporation_date')

    return render_to_response('eve_api/corporation.html', locals(), context_instance=RequestContext(request))
