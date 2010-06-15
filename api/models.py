import uuid

from django.db import models

class AuthAPIKey(models.Model):

    name = models.CharField("Service Name", max_length=200)
    url = models.CharField("Service URL", max_length=200, blank=True)
    active = models.BooleanField(default=True)
    key = models.CharField("API Key", max_length=200)

    def save(self, *args, **kwargs):
        if not key or key = '':
            self.key = uuid.uuid4()

        models.Model.save(self, *args, **kwargs)

class AuthAPILog(models.Model):

    access_datetime = models.DateTimeField()
    key = models.ForeignKey(AuthAPIKey)
    url = models.CharField("Accessed URL", max_length=200)
