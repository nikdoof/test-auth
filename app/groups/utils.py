from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.contrib.sites.models import Site

def send_group_email(request, to_email, subject, email_text_template, email_html_template):
    """Sends a email to a group of people using a standard layout"""

    # Mail the admins to inform them of a new request
    ctx = Context({'request': request, 'domain': Site.objects.get_current().domain})
    msg = EmailMultiAlternatives(subject, get_template(email_text_template).render(ctx), getattr(settings, 'DEFAULT_FROM_EMAIL', 'auth@pleaseignore.com'), to_email)
    msg.attach_alternative(get_template(email_html_template).render(ctx), 'text/html')
    msg.send(fail_silently=True)

