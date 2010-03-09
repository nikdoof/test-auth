from django import forms

from eve_api.models.api_player import EVEAccount
from sso.models import ServiceAccount, Service
from reddit.models import RedditAccount

class EveAPIForm(forms.Form):
    user_id = forms.IntegerField(label = u'User ID')
    api_key = forms.CharField(label = u'API Key', max_length=64)
    description = forms.CharField(max_length=100, required=False)

    def clean(self):
        if not len(self.cleaned_data['api_key']) == 64:
            raise forms.ValidationError("API Key provided is invalid (Not 64 characters long)")

        try:
            eaccount = EVEAccount.objects.get(api_user_id=self.cleaned_data['user_id'])
        except EVEAccount.DoesNotExist:
            return self.cleaned_data
        else:
            raise forms.ValidationError("This API User ID is already registered")

class ServiceUsernameField(forms.CharField):
    def clean(self, request, initial=None):
        field = super(ServiceUsernameField, self).clean(request)
        try:
            acc = ServiceAccount.objects.get(service_uid=field)
        except ServiceAccount.DoesNotExist:
            return field
        else:
            raise forms.ValidationError("That username is already taken")

def UserServiceAccountForm(user):
    """ Generate a Service Account form based on the user's permissions """

    services = Service.objects.filter(groups__in=user.groups.all())

    class ServiceAccountForm(forms.Form):
        service = forms.ModelChoiceField(queryset=services)
        username = ServiceUsernameField(min_length=4,max_length=50)
        password = forms.CharField(label = u'Password',widget = forms.PasswordInput(render_value=False)) 

    return ServiceAccountForm

class RedditAccountForm(forms.Form):
    username = forms.CharField(label = u'User ID', max_length=64)

    def clean(self):
        try:
            eaccount = RedditAccount.objects.get(username=self.cleaned_data['username'])
        except RedditAccount.DoesNotExist:
            return self.cleaned_data
        else:
            raise forms.ValidationError("This User ID is already registered")
