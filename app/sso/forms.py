import re

from django import forms
from django.contrib.auth.models import User
from django.conf import settings

from utils import installed

from eve_api.models import EVEAccount, EVEPlayerCharacter, EVEPlayerCorporation
from sso.models import ServiceAccount, Service
from registration.forms import RegistrationForm


class RegistrationFormUniqueEmailBlocked(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which disallows registration from certain
    domains and also makes sure that the email address is unique in the DB
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


def UserServiceAccountForm(user):
    """ Generate a Service Account form based on the user's permissions """

    services = Service.objects.filter(groups__in=user.groups.all(), active=1).exclude(id__in=ServiceAccount.objects.filter(user=user).values('service')).distinct()
    chars = EVEPlayerCharacter.objects.filter(eveaccount__user=user)

    class ServiceAccountForm(forms.Form):
        """ Service Account Form """

        character = forms.ModelChoiceField(queryset=chars, required=True, empty_label=None)
        service = forms.ModelChoiceField(queryset=services, required=True, empty_label=None)

        def __init__(self, *args, **kwargs):
            super(ServiceAccountForm, self).__init__(*args, **kwargs)
            if not settings.GENERATE_SERVICE_PASSWORD:
                self.password = forms.CharField(widget=forms.PasswordInput, label="Password")
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
    """ Password reset form for Services """

    def __init__(self, *args, **kwargs):
        super(ServiceAccountResetForm, self).__init__(*args, **kwargs)
        if not settings.GENERATE_SERVICE_PASSWORD:
            self.password = forms.CharField(widget=forms.PasswordInput, label="Password")
            self.fields['password'] = self.password


class UserLookupForm(forms.Form):
    """ User Lookup Form """

    def __init__(self, *args, **kwargs):
        super(UserLookupForm, self).__init__(*args, **kwargs)
        choices = [(1, "Auth Username"),
                   (2, "Character"),
                   (4, "Email Address"),
                   (5, "EVE API User ID"), ]
        if installed('reddit'):
            choices.append((3, "Reddit ID"))

        self.fields['type'] = forms.ChoiceField(label=u'Search type', choices=choices)
        self.fields['username'] = forms.CharField(label=u'User ID', max_length=64)


class APIPasswordForm(forms.Form):
    """ API Password reset form """

    password = forms.CharField(widget=forms.PasswordInput, label="Password")
