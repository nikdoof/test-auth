from django import forms

from sso.models import ServiceAccount, Service

class EveAPIForm(forms.Form):
    user_id = forms.CharField(max_length=10)
    api_key = forms.CharField(max_length=100)
    description = forms.CharField(max_length=100)

class ServiceUsernameField(forms.CharField):
    def clean(self, request, initial=None):
        field = super(ServiceUsernameField, self).clean(request)
        try:
            acc = ServiceAccount.objects.get(username=field)
        except ServiceAccount.DoesNotExist:
            return field
        else:
            raise forms.ValidationError("That username is already taken")

class ServiceAccountForm(forms.Form):
    service = forms.ModelChoiceField(queryset=Service.objects.filter(active=1), empty_label="Select A Service... ")
    username = ServiceUsernameField(min_length=4,max_length=50)
    password = forms.CharField(label = u'Password',widget = forms.PasswordInput(render_value=False)) 

