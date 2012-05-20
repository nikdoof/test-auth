from django import template
from django.utils.timezone import now
 
register = template.Library()
 
MOMENT = 120    # duration in seconds within which the time difference 
                # will be rendered as 'a moment ago'
 
@register.filter
def naturaltimediff(value):
    """
    Finds the difference between the datetime value given and now()
    and returns appropriate humanize form
    """
 
    from datetime import datetime
 
    if isinstance(value, datetime):
        delta = now() - value
        if delta.days > 6:
            return value.strftime("%b %d")                    # May 15
        if delta.days > 1:
            return value.strftime("%A")                       # Wednesday
        elif delta.days == 1:
            return 'yesterday'                                # yesterday
        elif delta.seconds > 3600:
            return str(delta.seconds / 3600 ) + ' hours ago'  # 3 hours ago
        elif delta.seconds >  MOMENT:
            return str(delta.seconds/60) + ' minutes ago'     # 29 minutes ago
        else:
            return 'a moment ago'                             # a moment ago
        return defaultfilters.date(value)
    else:
        return str(value)
