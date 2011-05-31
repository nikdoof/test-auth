from datetime import datetime

from django import forms
from django.conf import settings
from django.forms.extras.widgets import SelectDateWidget

from hr.app_defines import *
from hr.models import Application, Audit
from eve_api.models import EVEPlayerCharacter, EVEPlayerCorporation


def CreateRecommendationForm(user):
    """ Generate a Recommendation form based on the user's permissions """

    characters = EVEPlayerCharacter.objects.filter(eveaccount__user=user)
    applications = Application.objects.filter(status=APPLICATION_STATUS_NOTSUBMITTED)

    class RecommendationForm(forms.Form):
        """ Service Account Form """

        character = forms.ModelChoiceField(queryset=characters, required=True, empty_label=None)
        application = forms.ModelChoiceField(queryset=applications, required=True, empty_label=None)

    return RecommendationForm


def CreateApplicationForm(user):
    """ Generate a Application form based on the user's permissions """

    characters = EVEPlayerCharacter.objects.filter(eveaccount__user=user)
    corporations = EVEPlayerCorporation.objects.filter(application_config__is_accepting=True)

    class ApplicationForm(forms.Form):
        character = forms.ModelChoiceField(queryset=characters, required=True, empty_label=None)
        corporation = forms.ModelChoiceField(queryset=corporations, required=True, empty_label=None)

        def clean_character(self):
 
            if not 'character' in self.cleaned_data or not self.cleaned_data['character']:
                raise forms.ValidationError("Please select a character to apply with")

            if Application.objects.filter(character=self.cleaned_data['character']).exclude(status__in=[APPLICATION_STATUS_COMPLETED, APPLICATION_STATUS_REJECTED]).count():
                raise forms.ValidationError("This character already has a open application")

            return self.cleaned_data['character']


        def clean(self):

            char = self.cleaned_data.get('character')
            corp = self.cleaned_data.get('corporation')

            if char and corp:
                if char.corporation == corp:
                    raise forms.ValidationError("%s is already a member of %s" % (char, corp))
                if not char.account.api_keytype >= corp.application_config.api_required:
                    raise forms.ValidationError("%s requires a %s API key for this application" % (corp, corp.application_config.get_api_required_display()))

            return self.cleaned_data

    return ApplicationForm


class NoteForm(forms.ModelForm):
    class Meta:
        model = Audit
        exclude = ('application', 'user', 'event')


class BlacklistUserForm(forms.Form):
    """ A form to capture the reasons for blacklisting a user
        and the related expiry date """

    reason = forms.CharField(required=True, widget=forms.widgets.Textarea())
    expiry_date = forms.DateTimeField(required=False, widget=SelectDateWidget())
    disable = forms.BooleanField(required=False)
