import re

from django import forms
from gargoyle import gargoyle

from eve_api.models import EVEAccount, EVEPlayerCharacter, EVEPlayerCorporation


class EveAPIForm(forms.ModelForm):
    """ EVE API input form """

    class Meta:
        model = EVEAccount
        fields = ('api_user_id', 'api_key', 'description', 'user')
        widgets = {'user': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super(EveAPIForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        if instance and instance.pk:
            # We're editing a existing instance, readonly the userid
            self.fields['api_user_id'].widget.attrs['readonly'] = True

        if gargoyle.is_active('eve-cak'):
            self.fields['api_user_id'].label = 'Key ID'
            self.fields['api_key'].label = 'Verification Code'

    def clean_api_key(self):

        if not gargoyle.is_active('eve-cak') and not len(self.cleaned_data['api_key']) == 64:
            raise forms.ValidationError("Provided API Key is not 64 characters long.")

        if re.search(r'[^\.a-zA-Z0-9]', self.cleaned_data['api_key']):
            raise forms.ValidationError("Provided API Key has invalid characters.")

        return self.cleaned_data['api_key']

    def clean_api_user_id(self):

        if not 'api_user_id' in self.cleaned_data or self.cleaned_data['api_user_id'] == '':
            raise forms.ValidationError("Please provide a valid User ID")

        try:
            int(self.cleaned_data['api_user_id'])
        except ValueError:
            raise forms.ValidationError("Please provide a valid user ID.")

        if self.instance and self.instance.pk:
            if not int(self.cleaned_data['api_user_id']) == self.instance.api_user_id:
                raise forms.ValidationError("You cannot change your API User ID")
        else:
            try:
                eaccount = EVEAccount.objects.get(api_user_id=self.cleaned_data['api_user_id'])
            except EVEAccount.DoesNotExist:
                pass
            else:
                raise forms.ValidationError("This API User ID is already registered")

        return self.cleaned_data['api_user_id']
