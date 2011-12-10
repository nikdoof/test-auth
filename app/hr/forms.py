from datetime import datetime

from django import forms
from django.conf import settings
from django.forms.extras.widgets import SelectDateWidget

from django.contrib.auth.models import User
from hr.app_defines import *
from hr.models import Application, Audit, TemplateMessage
from eve_api.models import EVEPlayerCharacter, EVEPlayerCorporation
from eve_api.app_defines import API_STATUS_OK


class RecommendationForm(forms.Form):
    """ Add Recommendation Form """

    character = forms.ModelChoiceField(queryset=EVEPlayerCharacter.objects.all(), required=True, empty_label=None)
    application = forms.ModelChoiceField(queryset=Application.objects.filter(status=APPLICATION_STATUS_NOTSUBMITTED), required=True, empty_label=None)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(RecommendationForm, self).__init__(*args, **kwargs)
        self.fields['character'].queryset = EVEPlayerCharacter.objects.filter(eveaccount__user=user, eveaccount__api_status=API_STATUS_OK).distinct()

    def clean(self):
        char = self.cleaned_data.get('character')
        app = self.cleaned_data.get('application')

        if app.user in User.objects.filter(eveaccount__characters__id=char.id):
            raise forms.ValidationError("You cannot recommend your own character")

        return self.cleaned_data


class ApplicationForm(forms.Form):

    character = forms.ModelChoiceField(queryset=EVEPlayerCharacter.objects.all(), required=True, empty_label=None)
    corporation = forms.ModelChoiceField(queryset=EVEPlayerCorporation.objects.filter(application_config__is_accepting=True), required=True, empty_label=None)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.fields['character'].queryset = EVEPlayerCharacter.objects.filter(eveaccount__user=self.user, eveaccount__api_status=API_STATUS_OK).distinct()

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
                raise forms.ValidationError("%s is already a member of %s." % (char, corp))
            if not char.eveaccount_set.filter(user=self.user, api_keytype=corp.application_config.api_required).count():
                raise forms.ValidationError("%s requires a %s API key for this application." % (corp, corp.application_config.get_api_required_display()))
            if corp.application_config.api_accessmask:
                access = False
                for acc in char.eveaccount_set.filter(user=self.user, api_keytype=corp.application_config.api_required):
                    if acc.check_access(corp.application_config.api_accessmask):
                        access = True
                        break
                if not access:
                    raise forms.ValidationError("%s requires a API key with greater access than the one you have added, please add a key with the correct access." % (corp, corp.application_config.api_accessmask))

        return self.cleaned_data


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
