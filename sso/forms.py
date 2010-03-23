import re

from django import forms
from django.contrib.auth.models import User

from eve_api.models.api_player import EVEAccount, EVEPlayerCharacter
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

    services = Service.objects.filter(groups__in=user.groups.all()).exclude(id__in=ServiceAccount.objects.filter(user=user).values('service'))
    chars = EVEPlayerCharacter.objects.filter(corporation__group__in=user.groups.all(),eveaccount__user=user)

    class ServiceAccountForm(forms.Form):
        """ Service Account Form """

        character = forms.ModelChoiceField(queryset=chars, required=True, empty_label=None)
        service = forms.ModelChoiceField(queryset=services, required=True, empty_label=None)

        def clean(self):
            if not self.cleaned_data['character'].corporation.group in self.cleaned_data['service'].groups.all():
                raise forms.ValidationError("%s is not in a corporation allowed to access %s" % (self.cleaned_data['character'].name, self.cleaned_data['service']))

            return self.cleaned_data

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

    choices = [ (1, "Auth Username"),
                (2, "Character"),
                (3, "Reddit ID") ]

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
