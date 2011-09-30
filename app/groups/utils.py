from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

def send_group_mail(request, to_email, subject, email_text_template, email_html_template):
    """Sends a email to a group of people using a standard layout"""

    # Mail the admins to inform them of a new request
    ctx = Context({'request': obj})
    to_email = group.admins.values_list('email', flat=True)
    msg = EmailMultiAlternatives(subject, get_template(email_text_template).render(ctx), getattr(settings, 'SERVER_EMAIL', 'auth@pleaseignore.com'), to_email)
    msg.attach_alternative(get_template(email_html_template).render(ctx), 'text/html')
    mag.send(fail_silently=True)

