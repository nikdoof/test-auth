import uuid
from django.db import models


class AuthAPIKey(models.Model):
    """ Auth API Key storage model """

    name = models.CharField("Service Name", max_length=200)
    url = models.CharField("Service URL", max_length=200, blank=True, help_text="URL that the service is available at")
    active = models.BooleanField(default=True)
    key = models.CharField("API Key", max_length=200, blank=True, help_text="API key for the service to use")
    callback = models.CharField("Callback URL", max_length=200, blank=True, help_text="URL for the callback service to connect to")

    def save(self, *args, **kwargs):
        if not self.key or self.key == '':
            self.key = uuid.uuid4()

        models.Model.save(self, *args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = "API Keys"


class AuthAPILog(models.Model):
    """ Auth API Access Log """

    access_datetime = models.DateTimeField("Date/Time Accessed")
    key = models.ForeignKey(AuthAPIKey)
    url = models.CharField("Accessed URL", max_length=200)

    class Meta:
        ordering = ['access_datetime']
        verbose_name = 'API Access Log'
        verbose_name_plural = "API Access Logs"
