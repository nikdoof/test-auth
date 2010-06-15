from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from hashlib import sha1


class SimpleHashModelBackend(ModelBackend):

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if '$' in user.password:
            if user.check_password(password):
                user.password = sha1(password).hexdigest()
                user.save()
                return user
        else:
            if user.password == sha1(password).hexdigest():
                return user

        return None

