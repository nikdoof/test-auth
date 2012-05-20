import csv

from django.core import serializers
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.generic import DetailView, ListView
from django.contrib import messages
from django.contrib.auth.decorators import login_required

import celery
from gargoyle import gargoyle

from eve_proxy.models import ApiAccessLog, CachedDocument
from eve_proxy.exceptions import DocumentRetrievalError
from eve_api.app_defines import *
from eve_api.forms import EveAPIForm
from eve_api.models import EVEAccount, EVEPlayerCharacter, EVEPlayerCorporation, EVEPlayerAlliance
from eve_api.tasks import import_apikey_result
from eve_api.utils import basic_xml_parse_doc
from eve_api.views.mixins import DetailPaginationMixin


@login_required
def eveapi_add(request, post_save_redirect='/', template='eve_api/add.html'):
    """ Add a EVE API key to a user's account """

    if request.method == 'POST':
        form = EveAPIForm(request.POST)
        if form.is_valid():
            task = import_apikey_result.delay(api_key=form.cleaned_data['api_key'], api_userid=form.cleaned_data['api_user_id'], user=request.user.id)
            try:
                out = task.wait(10)
            except celery.exceptions.TimeoutError:
                msg = "The addition of your API key is still processing, please check back in a minute or so."
            except DocumentRetrievalError:
                msg = "An issue with the EVE API was encountered while adding your API, please try again later."
            except:
                msg = "An unknown error was encountered while trying to add your API key, please try again later."
            else:
                if out:
                    msg = "Key %d successfully added." % form.cleaned_data['api_user_id']
                else:
                    msg = "An issue was encountered while trying to import key %s, Please check that you are using the correct information and try again." % form.cleaned_data['api_user_id']
            messages.success(request, msg, fail_silently=True)
            return redirect(post_save_redirect)
    else:
        form = EveAPIForm(initial={'user': request.user.id }) # An unbound form

    context = {
        'form': form,
    }
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def eveapi_update(request, userid, post_save_redirect='/', template='eve_api/update.html'):
    """ Update a EVE API Key """

    acc = get_object_or_404(EVEAccount, pk=userid)
    if not acc.user == request.user and not request.user.is_staff:
        raise Http404    

    if request.method == 'POST':
        form = EveAPIForm(request.POST, instance=acc)
        if form.is_valid():
            if form.has_changed() and ('api_key' in form.changed_data):
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

    context = {
        'acc': acc,
        'form': form,
    }
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def eveapi_del(request, userid, post_save_redirect='/'):
    """ Delete a EVE API key from a account """

    if gargoyle.is_active('eve-keydelete', request):
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

    acc = get_object_or_404(EVEAccount, pk=userid)
    if acc.user == request.user or request.user.is_superuser:
        task = import_apikey_result.delay(api_key=acc.api_key, api_userid=acc.api_user_id, force_cache=True, user=request.user.id)
        if request.is_ajax():
            try:
                acc = task.wait(30)
            except (celery.exceptions.TimeoutError, DocumentRetrievalError):
                acc = EVEAccount.objects.get(pk=userid)
            ret = []
            if acc:
                ret = [acc]
            return HttpResponse(serializers.serialize('json', ret), mimetype='application/javascript')
        else:
            messages.add_message(request, messages.INFO, "Key %s has been queued to be refreshed from the API" % acc.api_user_id)

    return redirect(post_save_redirect)


class EVEAPILogView(ListView):

    model = ApiAccessLog
    template_name = 'eve_api/log.html'

    def dispatch(self, request, *args, **kwargs):
        self.userid = kwargs.pop('userid')
        if not (get_object_or_404(EVEAccount, pk=self.userid).user == request.user or request.user.is_superuser):
            raise Http404
        return super(EVEAPILogView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(EVEAPILogView, self).get_context_data(**kwargs)
        ctx.update({
            'userid': self.userid,
        })
        return ctx

    def get_queryset(self):
        limit = getattr(self, 'limit', 50)
        return self.model.objects.filter(userid=self.userid).order_by('-time_access')[:limit]


@login_required
def eveapi_character(request, charid=None, template='eve_api/character.html', list_template='eve_api/character_list.html'):
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
                skillTree.append([0, skill.skill.group.name, [], skill.skill.group.id])
            
            skillTree[-1][0] += skill.skillpoints
            skillTree[-1][2].append(skill)

        context = {
            'character': character,
            'current_training': current_training,
            'skills': skills,
            'skillTree': skillTree,
            'employmenthistory': character.employmenthistory.all().order_by('-record_id'),
        }
        return render_to_response(template, context, context_instance=RequestContext(request))

    context = {
        'accounts': EVEAccount.objects.select_related('characters__name').filter(user=request.user).exclude(api_keytype=API_KEYTYPE_CORPORATION),
        'characters': EVEPlayerCharacter.objects.filter(eveaccount__user=request.user).distinct().order_by('name'),
    }
    return render_to_response(list_template, context, context_instance=RequestContext(request))


class EVEAPICorporationView(DetailPaginationMixin, DetailView):

    model = EVEPlayerCorporation
    template_name = 'eve_api/corporation.html'
    detail_queryset_name = 'members'

    def get_pagination_queryset(self):
        return self.object.eveplayercharacter_set.select_related('eveaccount', 'roles').order_by('corporation_date').only('id', 'name', 'corporation_date')

    def get_context_data(self, **kwargs):
        ctx = super(EVEAPICorporationView, self).get_context_data(**kwargs)
        ctx.update({
            'corporation': self.object,
            'view_members': self.object.eveplayercharacter_set.filter(eveaccount__user=self.request.user, roles__name="roleDirector").count() or self.request.user.is_superuser,
        })
        return ctx


@login_required
def eveapi_corporation_members_csv(request, corporationid):

    corporation = get_object_or_404(EVEPlayerCorporation, id=corporationid)
    if not corporation.eveplayercharacter_set.filter(eveaccount__user=request.user, roles__name="roleDirector").count() and not request.user.is_superuser:
        raise Http404

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s-members_export.csv' % corporation.id

    writer = csv.writer(response)
    writer.writerow(['Name', 'Skillpoints', 'Join Date', 'Last Login', 'Director?', 'Roles?', 'API Key?'])
    for char in corporation.eveplayercharacter_set.all():
        writer.writerow([char.name, char.total_sp, char.corporation_date, char.last_login, char.director, char.roles.count(), char.eveaccount_set.all().count()])

    return response


class EVEAPIAllianceView(DetailPaginationMixin, DetailView):

    model = EVEPlayerAlliance
    template_name= 'eve_api/alliance.html'
    detail_queryset_name = 'corporations'

    def get_pagination_queryset(self):
        return self.object.eveplayercorporation_set.exclude(member_count=0).order_by('name')


    def get_context_data(self, **kwargs):
        ctx = super(EVEAPIAllianceView, self).get_context_data(**kwargs)
        ctx.update({
            'alliance': self.object,
            'executor': self.object.executor.ceo_character,
        })
        return ctx


class EVEAPIAccessView(DetailView):

    model = EVEAccount
    template_name = 'eve_api/accessview.html'
    slug_field = 'api_user_id'

    @staticmethod
    def lowestSet(int_type):
        low = (int_type & -int_type)
        lowBit = -1
        while (low):
            low >>= 1
            lowBit += 1
        return(lowBit)

    def get_context_data(self, **kwargs):
        ctx = super(EVEAPIAccessView, self).get_context_data(**kwargs)

        calls = basic_xml_parse_doc(CachedDocument.objects.api_query('/api/CallList.xml.aspx'))['eveapi']['result']
        if self.object.api_keytype == API_KEYTYPE_CORPORATION:
            typ = 'Corporation'
        else:
            typ = 'Character'

        ctx['access'] = []
        for row in [x for x in calls['calls'] if x['type'] == typ]:
            bit = self.lowestSet(int(row['accessMask']))
            ctx['access'].append((row['name'], self.object.has_access(bit)))

        return ctx
