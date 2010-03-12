import re

from django import forms
from django.contrib.auth.models import User

from eve_api.models.api_player import EVEAccount
from sso.models import ServiceAccount, Service
from reddit.models import RedditAccount

class EveAPIForm(forms.Form):
    """ EVE API input form """

    user_id = forms.IntegerField(label = u'User ID')
    api_key = forms.CharField(label = u'API Key', max_length=64)
    description = forms.CharField(max_length=100, required=False)

    def clean(self):
        if not len(self.cleaned_data['api_key']) == 64:
            raise forms.ValidationError("API Key provided is invalid (Not 64 characters long)")

        try:
            eaccount = EVEAccount.objects.get(api_user_id=self.cleaned_data['user_id'])
        except EVEAccount.DoesNotExist:
            return self.cleaned_data
        else:
            raise forms.ValidationError("This API User ID is already registered")

def UserServiceAccountForm(user):
    """ Generate a Service Account form based on the user's permissions """

    current_services = []
    for sa in ServiceAccount.objects.filter(user=user):
        current_services.append(sa.service)
    services = set(Service.objects.filter(groups__in=user.groups.all())) - set(current_services)

    eveacc = EVEAccount.objects.filter(user=user)
    chars = []
    for srv in services:
        for char in eveacc.characters.all():
            if char.corporation.group = srv.group and not char in chars:
                chars.append(char)

    class ServiceAccountForm(forms.Form):
        """ Service Account Form """

        character = forms.ChoiceField(chars)
        service = forms.ChoiceField(services)

    return ServiceAccountForm

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

    username = forms.CharField(label = u'User ID', max_length=64)

    def clean(self):
        try: 
            acc = User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            raise forms.ValidationError("User doesn't exist")
        return self.cleaned_data
