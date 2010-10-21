# Group Types
GROUP_TYPE_BUILTIN = 0
GROUP_TYPE_MANAGED = 1
GROUP_TYPE_PERMISSION = 2

GROUP_TYPE_CHOICES = (
    (GROUP_TYPE_BUILTIN, 'Built-In'),
    (GROUP_TYPE_PERMISSION, 'Permission'),
    (GROUP_TYPE_MANAGED, 'Managed'),
)


# Request Status Codes
REQUEST_PENDING = 0
REQUEST_ACCEPTED = 1
REQUEST_REJECTED = 2

REQUEST_STATUS_CHOICES = (
    (REQUEST_PENDING, 'Pending'),
    (REQUEST_ACCEPTED, 'Accepted'),
    (REQUEST_REJECTED, 'Rejected'),
)
