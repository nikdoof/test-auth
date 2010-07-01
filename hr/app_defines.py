
APPLICATION_STATUS_NOTSUBMITTED = 0
APPLICATION_STATUS_AWAITINGREVIEW = 1
APPLICATION_STATUS_REJECTED = 2
APPLICATION_STATUS_ACCEPTED = 3
APPLICATION_STATUS_QUERY = 4
APPLICATION_STATUS_COMPLETED = 5

APPLICATION_STATUS_CHOICES = (
    (APPLICATION_STATUS_NOTSUBMITTED, 'Not Submitted'),
    (APPLICATION_STATUS_AWAITINGREVIEW, 'Submitted'),
    (APPLICATION_STATUS_REJECTED, 'Rejected'),
    (APPLICATION_STATUS_ACCEPTED, 'Accepted'),
    (APPLICATION_STATUS_QUERY, 'In Query'),
    (APPLICATION_STATUS_COMPLETED, 'Completed'),
)

APPLICATION_STATUS_LOOKUP = {
    APPLICATION_STATUS_NOTSUBMITTED: 'Not Submitted',
    APPLICATION_STATUS_AWAITINGREVIEW: 'Submitted',
    APPLICATION_STATUS_REJECTED: 'Rejected',
    APPLICATION_STATUS_ACCEPTED: 'Accepted',
    APPLICATION_STATUS_QUERY: 'In Query',
    APPLICATION_STATUS_COMPLETED: 'Completed',
}    

AUDIT_EVENT_STATUSCHANGE = 0
AUDIT_EVENT_NOTE = 1
AUDIT_EVENT_REJECTION = 2
AUDIT_EVENT_ACCEPTED = 3
AUDIT_EVENT_MESSAGE = 4

AUDIT_EVENT_CHOICES = (
    (AUDIT_EVENT_STATUSCHANGE, 'Status Change'),
    (AUDIT_EVENT_NOTE, 'Staff Note'),
    (AUDIT_EVENT_REJECTION, 'Rejection Reason'),
    (AUDIT_EVENT_ACCEPTED, 'Accepted'),
    (AUDIT_EVENT_MESSAGE, 'Message to User'),
)

AUDIT_EVENT_LOOKUP = {
    AUDIT_EVENT_STATUSCHANGE: 'Status Change',
    AUDIT_EVENT_NOTE: 'Staff Note',
    AUDIT_EVENT_REJECTION: 'Rejection Reason',
    AUDIT_EVENT_ACCEPTED: 'Accepted',
    AUDIT_EVENT_MESSAGE: 'Message to User',
}

BLACKLIST_TYPE_REDDIT = 0
BLACKLIST_TYPE_CHARACTER = 1
BLACKLIST_TYPE_CORPORATION = 2
BLACKLIST_TYPE_ALLIANCE = 3
BLACKLIST_TYPE_EMAIL = 4

BLACKLIST_TYPE_CHOICES = (
    (BLACKLIST_TYPE_REDDIT, 'Reddit Account'),
    (BLACKLIST_TYPE_CHARACTER, 'Character'),
    (BLACKLIST_TYPE_CORPORATION, 'Corporation'),
    (BLACKLIST_TYPE_ALLIANCE, 'Alliance'),
    (BLACKLIST_TYPE_EMAIL, 'Email Address'),
)
