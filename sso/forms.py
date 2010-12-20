import re

from django import forms
from django.contrib.auth.models import User
from django.conf import settings

from eve_api.models import EVEAccount, EVEPlayerCharacter, EVEPlayerCorporation
from sso.models import ServiceAccount, Service
from reddit.models import RedditAccount
from registration.forms import RegistrationForm

class RegistrationFormUniqueEmailBlocked(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which disallows registration from certain domains
    and also makes sure that the email address is unique in the DB
    """

    def clean_email(self):
        """
        Check the supplied email address against a list of known free
        webmail domains.
        """

        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError("This email address is already in use. Please supply a different email address.")
        return self.cleaned_data['email']

        email_domain = self.cleaned_data['email'].split('@')[1]
        if email_domain in settings.BANNED_EMAIL_DOMAINS:
            raise forms.ValidationError("Your email provider (%s) is banned from registering, please use a different address.")
        return self.cleaned_data['email']


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

            form_data = self.cleaned_data
            service = form_data.get('service')
            character = form_data.get('character')

            if not service or not character:
                raise forms.ValidationError('Error while processing the form, please try again')

            service_groups = service.groups.all()

            # If the service's assigned groups are linked to corps, do a character/corp check
            if len(EVEPlayerCorporation.objects.filter(group__in=service_groups)):
                corp_group = character.corporation.group
                if character.corporation.alliance:
                    alliance_group = character.corporation.alliance.group
                else:
                    alliance_group = None

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

