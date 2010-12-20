from django import forms
from django.conf import settings

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
    corporations = EVEPlayerCorporation.objects.filter(applications=True)

    class ApplicationForm(forms.Form):
        character = forms.ModelChoiceField(queryset=characters, required=True, empty_label=None)
        corporation = forms.ModelChoiceField(queryset=corporations, required=True, empty_label=None)

        def clean(self):
 
            if not 'character' in self.cleaned_data or not self.cleaned_data['character']:
                raise forms.ValidationError("Please select a character to apply with")

            if len(Application.objects.filter(character=self.cleaned_data['character'], status__in=[APPLICATION_STATUS_NOTSUBMITTED, APPLICATION_STATUS_AWAITINGREVIEW, APPLICATION_STATUS_QUERY])):
                raise forms.ValidationError("This character already has a open application")

            return self.cleaned_data
    return ApplicationForm

class NoteForm(forms.ModelForm):

    class Meta:
        model = Audit
        exclude = ('application', 'user', 'event')
