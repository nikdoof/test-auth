from django import forms

from django.contrib.auth.models import User
from reddit.models import RedditAccount

class RedditAccountForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.order_by('username')) 
    username = forms.CharField(label = u'Reddit Username', max_length=64)

    def clean(self):
        try:
            eaccount = RedditAccount.objects.get(username=self.cleaned_data['username'])
        except RedditAccount.DoesNotExist:
            return self.cleaned_data
        else:
            raise forms.ValidationError("This User ID is already registered")
