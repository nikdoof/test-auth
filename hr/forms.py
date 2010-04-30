from django import forms
import settings

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
            if len(Application.objects.filter(character=self.cleaned_data['character'], status__in=[APPLICATION_STATUS_NOTSUBMITTED, APPLICATION_STATUS_AWAITINGREVIEW, APPLICATION_STATUS_QUERY])):
                raise forms.ValidationError("This character already has a open application")

            return self.cleaned_data
    return ApplicationForm

def CreateApplicationStatusForm(admin):

    if admin:
        form_choices = APPLICATION_STATUS_CHOICES_ADMIN
    else:
        form_choices = APPLICATION_STATUS_CHOICES_USER

    class ApplicationStatusForm(forms.Form):
        """ Application Status Change Form """

        application = forms.IntegerField(required=True, widget=forms.HiddenInput)
        new_status = forms.ChoiceField(label = u'New Status', choices = form_choices)

        class Meta:
            exclude = ('application')

    return ApplicationStatusForm


class NoteForm(forms.ModelForm):

    class Meta:
        model = Audit
        exclude = ('application', 'user', 'event')
