import re

from django import forms
from eve_api.models import EVEAccount, EVEPlayerCharacter, EVEPlayerCorporation


class EveAPIForm(forms.ModelForm):
    """ EVE API input form """

    class Meta:
        model = EVEAccount
        fields = ('api_user_id', 'api_key', 'description', 'user')
        widgets = {'user': forms.HiddenInput()}

    def clean_api_key(self):

        if not len(self.cleaned_data['api_key']) == 64:
            raise forms.ValidationError("Provided API Key is not 64 characters long.")

        if re.search(r'[^\.a-zA-Z0-9]', self.cleaned_data['api_key']):
            raise forms.ValidationError("Provided API Key has invalid characters.")

        return self.cleaned_data['api_key']

    def clean_user_id(self):

        if not 'user_id' in self.cleaned_data or self.cleaned_data['user_id'] == '':
            raise forms.ValidationError("Please provide a valid User ID")

        try:
            int(self.cleaned_data['user_id'])
        except ValueError:
            raise forms.ValidationError("Please provide a valid user ID.")

        if not self.update:
            try:
                eaccount = EVEAccount.objects.get(api_user_id=self.cleaned_data['user_id'])
            except EVEAccount.DoesNotExist:
                pass
            else:
                raise forms.ValidationError("This API User ID is already registered")

        return self.cleaned_data['user_id']
