from django import forms
import settings

from hr.app_defines import *
from hr.models import Application
from eve_api.models import EVEPlayerCharacter

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

    return ApplicationForm


