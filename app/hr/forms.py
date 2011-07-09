from datetime import datetime

from django import forms
from django.conf import settings
from django.forms.extras.widgets import SelectDateWidget

from hr.app_defines import *
from hr.models import Application, Audit, TemplateMessage
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

            if Application.objects.filter(character=self.cleaned_data['character']).exclude(status__in=[APPLICATION_STATUS_NOTSUBMITTED, APPLICATION_STATUS_COMPLETED, APPLICATION_STATUS_REJECTED]).count():
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


class AdminNoteForm(forms.ModelForm):

    template = forms.ModelChoiceField(label='Use Template', queryset=None, required=False, help_text="Use a predefined template text for this message")

    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application')
        super(AdminNoteForm, self).__init__(*args, **kwargs)
        self.fields['template'].queryset = TemplateMessage.objects.filter(config=self.application.corporation.application_config)
        self.fields['text'].required = False

    def clean(self):
        template = self.cleaned_data.get('template', None)
        if template:
            self.cleaned_data['text'] = template.render_template({'application': self.application})
        elif not self.cleaned_data.get('text', None):
            raise forms.ValidationError('You need to either select a template or fill in the message form')

        return self.cleaned_data

    class Meta:
        model = Audit
        exclude = ('application', 'user', 'event')


class BlacklistUserForm(forms.Form):
    """ A form to capture the reasons for blacklisting a user
        and the related expiry date """

    level = forms.ChoiceField(label="Blacklist Level", required=True, choices=BLACKLIST_LEVEL_CHOICES, help_text="The level of entry to be added to the account")
    reason = forms.CharField(label="Reason / Description", required=True, widget=forms.widgets.Textarea(), help_text="Brief description of why this account is being blacklisted")
    expiry_date = forms.DateTimeField(label="Expiry Date", required=False, widget=SelectDateWidget(), help_text="The date on which the blacklist entry should expire")
    disable = forms.BooleanField(label="Disable User?", required=False, help_text="Enabling this will disable the user's account once blacklisted")
