import re

from django import forms
from django.contrib.auth.models import User

from eve_api.models.api_player import EVEAccount
from sso.models import ServiceAccount, Service
from reddit.models import RedditAccount

class EveAPIForm(forms.Form):
    """ EVE API input form """

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
    """ Extension of a CharField, does extra validation on username format and
        also checks the username is free with ServiceAccount model """

    def clean(self, request, initial=None):
        field = super(ServiceUsernameField, self).clean(request)

        # Checks that usernames consist of letters and numbers only
        if not re.match("^[A-Za-z0-9_-]*$", field):
            raise forms.ValidationError("Invalid character in username, use letters and numbers only")

        return field

def UserServiceAccountForm(user):
    """ Generate a Service Account form based on the user's permissions """

    services = Service.objects.filter(groups__in=user.groups.all())

    class ServiceAccountForm(forms.Form):
        """ Service Account Form """

        service = forms.ModelChoiceField(queryset=services)
        username = ServiceUsernameField(min_length=4,max_length=50)
        password = forms.CharField(label = u'Password',widget = forms.PasswordInput(render_value=False)) 

        def clean(self):
            try:
                acc = ServiceAccount.objects.get(service_uid=self.cleaned_data['username'],service=self.cleaned_data['service'])
            except ServiceAccount.DoesNotExist:
                pass
            else:
                raise forms.ValidationError("That username is already taken")
            return self.cleaned_data


    return ServiceAccountForm

class RedditAccountForm(forms.Form):
    """ Reddit Account Form """

    username = forms.CharField(label = u'User ID', max_length=64)

    def clean(self):
        try:
            eaccount = RedditAccount.objects.get(username=self.cleaned_data['username'])
        except RedditAccount.DoesNotExist:
            return self.cleaned_data
        else:
            raise forms.ValidationError("This User ID is already registered")

class UserLookupForm(forms.Form):
    """ User Lookup Form """

    username = forms.CharField(label = u'User ID', max_length=64)

    def clean(self):
        try: 
            acc = User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            raise forms.ValidationError("User doesn't exist")
        return self.cleaned_data
