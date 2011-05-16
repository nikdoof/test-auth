from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from hashlib import sha1


class SimpleHashModelBackend(ModelBackend):

    supports_anonymous_user = False
    supports_object_permissions = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if '$' in user.password:
            if user.check_password(password):
                return user
        else:
            if user.password == sha1(password).hexdigest():
		user.set_password(password)
                return user

        return None
