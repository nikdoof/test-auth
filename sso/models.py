from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User

from sso.service import get_api

class Service(models.Model):
    url = models.CharField(max_length=200)
    active = models.BooleanField()
    api = models.CharField(max_length=200)

class ServiceAccount(models.Model):
    user = models.ForeignKey(User,blank=False)
    service = models.ForeignKey(Service,blank=False)
    username = models.CharField(max_length=200,blank=False)
    active = models.BooleanField()

    def save(self):
        """ Override default save to setup accounts as needed """

        if not self.service:
            raise DoesNotExist('No Service set on this account!')

        if not self.user:
            raise DoesNotExist('No User set on this account!')

        if not self.username:
            self.username = self.user.name

        api = get_api(self.service.api)

        if self.active:
            if not api.check_user(self.username):
                api.add_user(self.username, self.password)
        else:
            if api.check_user(self.username):
                api.del_user(self.username)

        # All went OK, save to the DB
        return models.Model.save(self)

    @staticmethod
    def pre_delete_listener( **kwargs ):
        api = get_api(kwargs['instance'].service.api)
        if api.check_user(kwargs['instance'].username):
            api.del_user(kwargs['instance'].username)

signals.pre_delete.connect(ServiceAccount.pre_delete_listener, sender=ServiceAccount)
