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

API_RACES = {
    'Caldari': 1,
    'Minmatar': 2,
    'Gallente': 3,
    'Amarr': 4, 
}

API_BLOODLINES = {
    'Sebiestor': 1,
    'Vherokior': 2,
    'Brutor': 3,
    'Intaki': 4,
    'Gallente': 5,
    'Jin-Mei': 6,
    'Civire': 7,
    'Deteis': 8,
    'Achura': 9,
    'Amarr': 10,
    'Khanid': 11,
    'Ni-Kunni': 12,
}
