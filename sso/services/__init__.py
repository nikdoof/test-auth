
def get_api(api):
    try:
        mod = __import__(self.service.api)
    except ImportError:
        raise DoesNotExist('Error creating service')

    for i in self.service.api.spit(".")[1:]:
        mod = getattr(mod, i)

    return getattr(mod, mod.ServiceClass)()


class BaseService():
    """
    Base Service class, all service classes should inherit from this

    """

    def add_user(self, username, password):
        """ Add a user """
        pass

    def set_corp(self, username):
        """ User is in corp, enable extra privs """
        pass

    def delete_user(self, username):
        """ Delete a user """
        pass

    def disable_user(self, username):
        """ Disable a user """
        pass

    def enable_user(self, username):
        """ Enable a user """       
        pass

    def check_user(self, username):
        """ Check if the username exists """
        pass
