import settings

def get_api(api):

    if settings.DISABLE_SERVICES:
        return BaseService()

    try:
        mod = __import__(api)
    except ImportError:
        raise Exception('Error creating service')

    for i in api.split(".")[1:]:
        mod = getattr(mod, i)

    return getattr(mod, mod.ServiceClass)()


class BaseService():
    """
    Base Service class, all service classes should inherit from this

    """

    settings = { 'require_user': True,
                 'require_password': True,
                 'provide_login': False }

    def add_user(self, username, password):
        """ Add a user """
        pass

    def delete_user(self, username):
        """ Delete a user """
        pass

    def disable_user(self, username):
        """ Disable a user """
        pass

    def enable_user(self, username, password):
        """ Enable a user """       
        pass

    def check_user(self, username):
        """ Check if the username exists """
        pass

    def login(username):
        """ Login the user and provide cookies back """ 
        pass
