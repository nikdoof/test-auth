from django import forms
import settings

from groups.models import GroupRequest
from groups.app_defines import *

class GroupRequestForm(forms.ModelForm):

    class Meta:
        model = GroupRequest
        exclude = ('group', 'user', 'status', 'changed_by', 'changed_date', 'created_date')
