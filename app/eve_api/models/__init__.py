"""
By importing all of these sub-modules, the models package is transparently
accessible by the rest of the project. This makes it act just as if it were
one monolithic models.py.
"""

from django.db import models

class EVEAPIModel(models.Model):
    """
    A simple abstract base class to set some consistent fields on the models
    that are updated from the EVE API.
    """
    api_last_updated = models.DateTimeField(blank=True, null=True,
                                            verbose_name="Time last updated from API",
                                            help_text="When this object was last updated from the EVE API.")

    class Meta:
        abstract = True


from static import *
from account import *
from character import *
from corporation import *
from alliance import *
