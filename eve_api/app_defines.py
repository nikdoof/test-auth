"""
Standard definitions that don't change.
"""
# API status definitions for EVEAccount.
API_STATUS_PENDING = 0
API_STATUS_OK = 1
API_STATUS_AUTH_ERROR = 2
API_STATUS_OTHER_ERROR = 3
API_STATUS_ACC_EXPIRED = 4
# This tuple is used to assemble the choices list for the field.
API_STATUS_CHOICES = (
    (API_STATUS_PENDING, 'Unknown'),
    (API_STATUS_OK, 'OK'),
    (API_STATUS_AUTH_ERROR, 'Auth Error'),
    (API_STATUS_OTHER_ERROR, 'Other Error'),
    (API_STATUS_ACC_EXPIRED, 'Account Expired'),
)

API_KEYTYPE_UNKNOWN = 0
API_KEYTYPE_LIMITED = 1
API_KEYTYPE_FULL = 2

API_KEYTYPE_CHOICES = (
    (API_KEYTYPE_UNKNOWN, 'Unknown'),
    (API_KEYTYPE_LIMITED, 'Limited'),
    (API_KEYTYPE_FULL, 'Full'),
)

API_GENDER_CHOICES = (
    (1, 'Male'),
    (2, 'Female'),
)

API_RACES_CHOICES = (
    (1, 'Caldari'),
    (2, 'Minmatar'),
    (3, 'Gallente'),
    (4, 'Amarr'),
)

API_BLOODLINES_CHOICES = (
    (1, 'Sebiestor'),
    (2, 'Vherokior'),
    (3, 'Brutor'),
    (4, 'Intaki'),
    (5, 'Gallente'),
    (6, 'Jin-Mei'),
    (7, 'Civire'),
    (8, 'Deteis'),
    (9, 'Achura'),
    (10, 'Amarr'),
    (11, 'Khanid'),
    (12, 'Ni-Kunni'),
    (13, 'Caldari'),
)
