from sso.services import BaseService

class DummyService(BaseService):
    """ Always passes, good for a test service """
    pass


ServiceClass = 'DummyService'
