"""
Admin interface models. Automatically detected by admin.autodiscover().
"""
from django.contrib import admin
from sso.models import Service, ServiceAccount

admin.site.register(Service)
admin.site.register(ServiceAccount)
