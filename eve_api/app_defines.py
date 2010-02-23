"""
Standard definitions that don't change.
"""
# API status definitions for EVEAccount.
API_STATUS_PENDING = 0
API_STATUS_OK = 1
API_STATUS_AUTH_ERROR = 2
API_STATUS_OTHER_ERROR = 3
# This tuple is used to assemble the choices list for the field.
API_STATUS_CHOICES = (
    (API_STATUS_PENDING, 'Unknown'),
    (API_STATUS_OK, 'OK'),
    (API_STATUS_AUTH_ERROR, 'Auth Error'),
    (API_STATUS_OTHER_ERROR, 'Other Error'),
)