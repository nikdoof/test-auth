from django.db import models
from django.contrib.auth.models import User
from eve_api.app_defines import *
from eve_api.models import EVEAPIModel

class EVEAccount(EVEAPIModel):
    """
    Use this class to store EVE user account information. Note that its use is
    entirely optional and up to the developer's discretion.
    """
    user = models.ForeignKey(User, blank=True, null=True,
                             help_text="User that owns this account")
    description = models.CharField(max_length=50, blank=True,
                                   help_text="User-provided description.")
    api_key = models.CharField(max_length=64, verbose_name="API Key",
                               help_text="EVE API Key")
    api_user_id = models.IntegerField(verbose_name="API User ID",
                                      help_text="EVE API User ID")
    characters = models.ManyToManyField('eve_api.EVEPlayerCharacter', blank=True, null=True)
    api_status = models.IntegerField(choices=API_STATUS_CHOICES,
                                     default=API_STATUS_PENDING,
                                     verbose_name="API Status",
                                     help_text="End result of the last attempt at updating this object from the API.")
    api_keytype = models.IntegerField(choices=API_KEYTYPE_CHOICES,
                                     default=API_KEYTYPE_UNKNOWN,
                                     verbose_name="API Key Type",
                                     help_text="Type of API key")

    def __unicode__(self):
        return u"%s" % self.id

    def in_corp(self, corpid):
        return self.character.filter(corporation__id=corpid).count()

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'EVE Account'
        verbose_name_plural = 'EVE Accounts'
        ordering = ['api_user_id']

