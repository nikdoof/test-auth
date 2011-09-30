from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import get_template
from django.template import Context
from django.contrib.sites.models import Site

def send_group_email(request, to_email, subject, email_text_template, email_html_template):
    """Sends a email to a group of people using a standard layout"""

    # Mail the admins to inform them of a new request
    ctx = Context({'request': request, 'domain': Site.objects.get_current().domain})

    messages = [generate_mail(ctx, email_text_template, email_html_template, to, subject) for to in to_email]
    connection = get_connection(fail_silently=True)
    connection.send_messages(messages)

def generate_mail(context, email_text_template, email_html_template, to, subject):
    msg = EmailMultiAlternatives(subject, get_template(email_text_template).render(context), getattr(settings, 'DEFAULT_FROM_EMAIL', 'auth@pleaseignore.com'), [to])
    msg.attach_alternative(get_template(email_html_template).render(context), 'text/html')
    return msg

