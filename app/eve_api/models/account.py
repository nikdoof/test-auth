from django.db import models
from django.contrib.auth.models import User
from gargoyle import gargoyle
from eve_api.app_defines import *
from eve_api.models import EVEAPIModel

class EVEAccount(EVEAPIModel):
    """
    Use this class to store EVE user account information. Note that its use is
    entirely optional and up to the developer's discretion.
    """
    api_user_id = models.IntegerField(primary_key=True, verbose_name="API User ID",
                                      help_text="EVE API User ID")
    api_key = models.CharField(max_length=64, verbose_name="API Key",
                               help_text="EVE API Key")

    user = models.ForeignKey(User, blank=True, null=True,
                             help_text="User that owns this account")
    description = models.CharField(max_length=50, blank=True,
                                   help_text="User-provided description.")
    characters = models.ManyToManyField('eve_api.EVEPlayerCharacter', blank=True, null=True)
    api_status = models.IntegerField(choices=API_STATUS_CHOICES,
                                     default=API_STATUS_PENDING,
                                     verbose_name="API Status",
                                     help_text="End result of the last attempt at updating this object from the API.")
    api_keytype = models.IntegerField(choices=API_KEYTYPE_CHOICES,
                                     default=API_KEYTYPE_UNKNOWN,
                                     verbose_name="API Key Type",
                                     help_text="Type of API key")
    api_accessmask = models.IntegerField(default=0,
                                         verbose_name="API Key Access Mask",
                                         help_text="Describes the level of access this API key gives to the user's data")
    api_expiry = models.DateTimeField(blank=True, null=True,
                                      verbose_name="API Key Expiry Date",
                                       help_text="Indicates when the API key will expire.")

    def __unicode__(self):
        return u"%s" % self.pk

    def in_corp(self, corpid):
        return self.character.filter(corporation__id=corpid).count()

    @staticmethod
    def _mask_check(accessmask, bit):
        """ Returns a bool indicating if the bit is set in the accessmask """
        mask = 1 << bit
        return (accessmask & mask) > 0

    def has_access(self, bit):
        """ Checks if a specific bit is enabled in the key's access mask """
        if gargoyle.is_active('eve-cak') and self.is_cak:
            return self._mask_check(self.api_accessmask, bit)
        else:
            return True

    def check_access(self, accessmask):
        """ Checks if the account has equal or higher access than the bitmask provided """

        length = 0
        i = accessmask
        while i:
            i >>= 1
            length += 1

        for bit in range(0, length-1):
            if self._mask_check(accessmask, bit) and not self.has_access(bit):
                return False

        return True

    @property
    def training(self):
        return self.characters.filter(eveplayercharacterskill__in_training__gt=0).count()

    @property
    def is_cak(self):
        return self.api_keytype in [API_KEYTYPE_UNKNOWN, API_KEYTYPE_CHARACTER, API_KEYTYPE_CORPORATION, API_KEYTYPE_ACCOUNT]

    class Meta:
        app_label = 'eve_api'
        verbose_name = 'EVE API Key'
        verbose_name_plural = 'EVE API Keys'
        ordering = ['api_user_id']

