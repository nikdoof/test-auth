
APPLICATION_STATUS_NOTSUBMITTED = 0
APPLICATION_STATUS_AWAITINGREVIEW = 1
APPLICATION_STATUS_REJECTED = 2
APPLICATION_STATUS_ACCEPTED = 3
APPLICATION_STATUS_QUERY = 4
APPLICATION_STATUS_COMPLETED = 5

APPLICATION_STATUS_CHOICES = (
    (APPLICATION_STATUS_NOTSUBMITTED, 'Not Submitted'),
    (APPLICATION_STATUS_AWAITINGREVIEW, 'Awaiting Review'),
    (APPLICATION_STATUS_REJECTED, 'Rejected'),
    (APPLICATION_STATUS_ACCEPTED, 'Accepted'),
    (APPLICATION_STATUS_QUERY, 'In Query'),
    (APPLICATION_STATUS_COMPLETED, 'Completed'),
)
