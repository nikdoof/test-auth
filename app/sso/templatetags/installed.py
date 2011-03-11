from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def installed(value):
    apps = settings.INSTALLED_APPS
    if "." in value:
        for app in apps:
            if app == value:
                return True
    else:
        for app in apps:
            fields = app.split(".")
            if fields[-1] == value:
                return True
    return False
