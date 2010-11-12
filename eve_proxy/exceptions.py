class DocumentRetrievalError(Exception):
    """
    Unable to retrieve a document from the EVE API: %s
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.__doc__ % value

class InvalidDocument(Exception):
    """
    The document retrieved from the EVE API is not a valid XML document
    """
    def __str__(self):
        return self.__doc__

