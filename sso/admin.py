"""
Admin interface models. Automatically detected by admin.autodiscover().
"""
from django.contrib import admin
from sso.models import *

admin.site.register(sso.models.Service)
