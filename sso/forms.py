import re

from django import forms
from django.contrib.auth.models import User

import settings
from eve_api.models.api_player import EVEAccount, EVEPlayerCharacter, EVEPlayerCorporation
from sso.models import ServiceAccount, Service
from reddit.models import RedditAccount

class EveAPIForm(forms.Form):
    """ EVE API input form """

    user_id = forms.IntegerField(label = u'User ID')
    api_key = forms.CharField(label = u'API Key', max_length=64)
    description = forms.CharField(max_length=100, required=False)

    def clean(self):

        if not 'api_key' in self.cleaned_data or not len(self.cleaned_data['api_key']) == 64:
            raise forms.ValidationError("API Key provided is invalid (Not 64 characters long)")

        if not 'user_id' in self.cleaned_data:
            raise forms.ValidationError("Please provide a valid User ID")

        try:
            eaccount = EVEAccount.objects.get(api_user_id=self.cleaned_data['user_id'])
        except EVEAccount.DoesNotExist:
            return self.cleaned_data
        else:
            raise forms.ValidationError("This API User ID is already registered")

def UserServiceAccountForm(user):
    """ Generate a Service Account form based on the user's permissions """

    services = Service.objects.filter(groups__in=user.groups.all(),active=1).exclude(id__in=ServiceAccount.objects.filter(user=user).values('service')).distinct()
    chars = EVEPlayerCharacter.objects.filter(eveaccount__user=user)

    print len(services)

    class ServiceAccountForm(forms.Form):
        """ Service Account Form """

        character = forms.ModelChoiceField(queryset=chars, required=True, empty_label=None)
        service = forms.ModelChoiceField(queryset=services, required=True, empty_label=None)

        def __init__(self, *args, **kwargs):
            super(ServiceAccountForm, self).__init__(*args, **kwargs)
            if not settings.GENERATE_SERVICE_PASSWORD:
                self.password = forms.CharField(widget=forms.PasswordInput, label="Password" )
                self.fields['password'] = self.password

        def clean(self):
            # If the service's assigned groups are linked to corps, do a character/corp check
            if len(EVEPlayerCorporation.objects.filter(group__in=self.cleaned_data['service'].groups.all())):
                corp_group = self.cleaned_data['character'].corporation.group
                if self.cleaned_data['character'].corporation.alliance:
                    alliance_group = self.cleaned_data['character'].corporation.alliance.group
                else:
                    alliance_group = None
                service_groups = self.cleaned_data['service'].groups.all()

                if not (corp_group in service_groups or alliance_group in service_groups):
                    raise forms.ValidationError("%s is not in a corporation or alliance allowed to register for %s" % (self.cleaned_data['character'].name, self.cleaned_data['service']))

            return self.cleaned_data

    return ServiceAccountForm

class ServiceAccountResetForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ServiceAccountResetForm, self).__init__(*args, **kwargs)
        if not settings.GENERATE_SERVICE_PASSWORD:
            self.password = forms.CharField(widget=forms.PasswordInput, label="Password" )
            self.fields['password'] = self.password

class RedditAccountForm(forms.Form):
    """ Reddit Account Form """

    username = forms.CharField(label = u'User ID', max_length=64)

    def clean(self):
        try:
            eaccount = RedditAccount.objects.get(username=self.cleaned_data['username'])
        except RedditAccount.DoesNotExist:
            return self.cleaned_data
        else:
            raise forms.ValidationError("This User ID is already registered")

class UserLookupForm(forms.Form):
    """ User Lookup Form """

    choices = [ (1, "Auth Username"),
                (2, "Character"),
                (3, "Reddit ID"),
                (4, "Email Address"), ]

    type = forms.ChoiceField(label = u'Search type', choices = choices)
    username = forms.CharField(label = u'User ID', max_length=64)

    def clean(self):

        if self.cleaned_data['type'] == 1:
            try: 
                acc = User.objects.filter(username=self.cleaned_data['username'])
            except User.DoesNotExist:
                raise forms.ValidationError("User doesn't exist")
        elif self.cleaned_data['type'] == 2:
            try:
                acc = EVEPlayerCharacter.filter(name=self.cleaned_data['username'])
            except User.DoesNotExist:
                raise forms.ValidationError("Character doesn't exist")
        elif self.cleaned_data['type'] == 3:
            try:
                acc = RedditAccount.filter(name=self.cleaned_data['username'])
            except User.DoesNotExist:
                raise forms.ValidationError("Account doesn't exist")

        return self.cleaned_data

class APIPasswordForm(forms.Form):

    password = forms.CharField(widget=forms.PasswordInput, label="Password" )

