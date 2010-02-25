from django import forms

from sso.models import ServiceAccount

class EveAPIForm(forms.Form):
    user_id = forms.CharField(max_length=10)
    api_key = forms.CharField(max_length=100)
    description = forms.CharField(max_length=100)

class ServiceAccountForm(forms.ModelForm):
    class Meta:
        model = ServiceAccount
        exclude = ['user', 'active']

