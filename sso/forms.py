from django import forms

from eve_api.models.api_player import EVEAccount
from sso.models import ServiceAccount, Service
from reddit.models import RedditAccount

class EveAPIForm(forms.Form):
    user_id = forms.CharField(label = u'User ID', max_length=10)
    api_key = forms.CharField(label = u'API Key', max_length=100)
    description = forms.CharField(max_length=100)

    def clean(self):
        if not self.cleaned_data['user_id'].isdigit():
            raise forms.ValidationError("API User ID provided is not valid")

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
            acc = ServiceAccount.objects.get(username=field)
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
