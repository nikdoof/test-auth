from django import forms

from reddit.models import RedditAccount


class RedditAccountForm(forms.ModelForm):
    """ Basic Reddit account input form """

    def clean(self):
        try:
            eaccount = RedditAccount.objects.get(username=self.cleaned_data['username'])
        except RedditAccount.DoesNotExist:
            return self.cleaned_data
        else:
            raise forms.ValidationError("This User ID is already registered")

    class Meta:
        model = RedditAccount
        fields = ('username', 'user')
        widgets = {'user': forms.HiddenInput()}
