# Permission Levels
HR_NONE = 0
HR_VIEWONLY = 1
HR_ADMIN = 2

# Application Status Codes
APPLICATION_STATUS_NOTSUBMITTED = 0
APPLICATION_STATUS_AWAITINGREVIEW = 1
APPLICATION_STATUS_REJECTED = 2
APPLICATION_STATUS_ACCEPTED = 3
APPLICATION_STATUS_QUERY = 4
APPLICATION_STATUS_COMPLETED = 5
APPLICATION_STATUS_FLAGGED = 6

APPLICATION_STATUS_CHOICES = (
    (APPLICATION_STATUS_NOTSUBMITTED, 'Not Submitted'),
    (APPLICATION_STATUS_AWAITINGREVIEW, 'Submitted'),
    (APPLICATION_STATUS_REJECTED, 'Rejected'),
    (APPLICATION_STATUS_ACCEPTED, 'Accepted'),
    (APPLICATION_STATUS_QUERY, 'In Query'),
    (APPLICATION_STATUS_COMPLETED, 'Completed'),
    (APPLICATION_STATUS_FLAGGED, 'Flagged For Review'),
)

# Routes that are allowed (Accept/Reject are managed seperately)
APPLICATION_STATUS_ROUTES = {
    APPLICATION_STATUS_NOTSUBMITTED: [APPLICATION_STATUS_AWAITINGREVIEW],
    APPLICATION_STATUS_AWAITINGREVIEW: [APPLICATION_STATUS_NOTSUBMITTED, APPLICATION_STATUS_QUERY, APPLICATION_STATUS_FLAGGED],
    APPLICATION_STATUS_REJECTED: [APPLICATION_STATUS_NOTSUBMITTED],
    APPLICATION_STATUS_ACCEPTED: [APPLICATION_STATUS_NOTSUBMITTED, APPLICATION_STATUS_COMPLETED],
    APPLICATION_STATUS_QUERY: [APPLICATION_STATUS_NOTSUBMITTED, APPLICATION_STATUS_FLAGGED],
    APPLICATION_STATUS_COMPLETED: [],
    APPLICATION_STATUS_FLAGGED: [APPLICATION_STATUS_NOTSUBMITTED, APPLICATION_STATUS_QUERY],
}

# Audit Event Type Codes
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
    (AUDIT_EVENT_MESSAGE, 'Message'),
)

# Blacklist Type Codes
BLACKLIST_TYPE_REDDIT = 0
BLACKLIST_TYPE_CHARACTER = 1
BLACKLIST_TYPE_CORPORATION = 2
BLACKLIST_TYPE_ALLIANCE = 3
BLACKLIST_TYPE_EMAIL = 4
BLACKLIST_TYPE_AUTH = 5
BLACKLIST_TYPE_APIUSERID = 6

BLACKLIST_TYPE_CHOICES = (
    (BLACKLIST_TYPE_REDDIT, 'Reddit Account'),
    (BLACKLIST_TYPE_CHARACTER, 'Character'),
    (BLACKLIST_TYPE_CORPORATION, 'Corporation'),
    (BLACKLIST_TYPE_ALLIANCE, 'Alliance'),
    (BLACKLIST_TYPE_EMAIL, 'Email Address'),
    (BLACKLIST_TYPE_AUTH, 'Auth Account'),
    (BLACKLIST_TYPE_APIUSERID, 'EVE API User ID'),
)

BLACKLIST_SOURCE_INTERNAL = 0
BLACKLIST_SOURCE_EXTERNAL = 1

BLACKLIST_SOURCE_CHOICES = (
    (BLACKLIST_SOURCE_INTERNAL, 'Internal'),
    (BLACKLIST_SOURCE_EXTERNAL, 'External'),
)

BLACKLIST_LEVEL_BLACKLIST = 0
BLACKLIST_LEVEL_WARNING = 1
BLACKLIST_LEVEL_ADVISORY = 2
BLACKLIST_LEVEL_NOTE = 3

BLACKLIST_LEVEL_CHOICES = (
    (BLACKLIST_LEVEL_BLACKLIST, 'Blacklist'),
    (BLACKLIST_LEVEL_WARNING, 'Warning'),
    (BLACKLIST_LEVEL_ADVISORY, 'Advisory'),
    (BLACKLIST_LEVEL_NOTE, 'Note'),
)
