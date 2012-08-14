"""
Contains exeptions used in the eve_api app.
"""
class APIAuthException(Exception):
    """
    Raised when an invalid userID and/or authKey were provided.
    """
    def __str__(self):
        return "An authentication was encountered while querying the EVE API."
    
class APINoUserIDException(Exception):
    """
    Raised when a userID is required, but missing.
    """
    def __str__(self):
        return "This query requires a valid userID, but yours is either missing or invalid."

class APIAccessException(Exception):
    """
    Raised on Access errors of any kind, network and EVE API failures
    """

    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, msg)

    def __str__(self):
        return "An error was encountered while accessing the EVE API: %s" % self.msg
