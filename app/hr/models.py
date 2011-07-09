from datetime import datetime
from django.conf import settings
from django.db import models
from django.template import Template, Context
from django.contrib.auth.models import User
from eve_api.models import EVEPlayerCharacter, EVEPlayerCorporation
from eve_api.app_defines import *
from hr.app_defines import *

class Application(models.Model):
    """ Person's application to a corporation """

    user = models.ForeignKey(User, blank=False, verbose_name="User")
    character = models.ForeignKey(EVEPlayerCharacter, blank=False,
                                  verbose_name="Character")
    corporation = models.ForeignKey(EVEPlayerCorporation, blank=False,
                                    verbose_name="Applying to Corporation")
    status = models.IntegerField(choices=APPLICATION_STATUS_CHOICES,
                                     default=APPLICATION_STATUS_NOTSUBMITTED,
                                     verbose_name="Status",
                                     help_text="Current status of this application request.")
    application_date = models.DateTimeField(auto_now_add=True, verbose_name="Created Date")

    @models.permalink
    def get_absolute_url(self):
        return ('hr.views.view_application', [self.id])

    @property
    def blacklisted(self):
        return len([x for x in self.blacklist_values if x.level == BLACKLIST_LEVEL_BLACKLIST]) > 0

    @property
    def blacklist_values(self):
        if not hasattr(self, '_blcache'):
            from hr.utils import blacklist_values
            self._blcache = blacklist_values(self.user)
        return self._blcache

    @property
    def last_action(self):
        if self.audit_set.count():
            return self.audit_set.all().order_by('-date')[0]
        return None

    @property
    def alt_application(self):
        if EVEPlayerCharacter.objects.filter(corporation=self.corporation, eveaccount__user=self.user).count() > 0:
            return True
        return False

    def save(self, *args, **kwargs):

        user = kwargs.pop('user', None)
        try:
            old_instance = Application.objects.get(id=self.id)
            if not (old_instance.status == int(self.status)):
                event = Audit(application=self)
                event.user = user
                event.event = AUDIT_EVENT_STATUSCHANGE

                # Save the application so we can get a up to date status
                super(Application, self).save(*args, **kwargs)
                new_instance = Application.objects.get(id=self.id)

                event.text = "Status changed from %s to %s" % (old_instance.get_status_display(), new_instance.get_status_display())
                event.save()
        except:
            pass

        super(Application, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.character.name

    class Meta:
        permissions = (
            ("can_accept", "Can accept / reject applications"),
            ("can_view_all", "Can view all applications"),
            ("can_view_corp", "Can view corp applications"),
        )

class Recommendation(models.Model):
    """ User recommendation for a application """

    user = models.ForeignKey(User, blank=False, verbose_name="User")
    user_character = models.ForeignKey(EVEPlayerCharacter, blank=False, verbose_name="Recommender")
    application = models.ForeignKey(Application, blank=False, verbose_name="Recommended Application")
    recommendation_date = models.DateTimeField(auto_now_add=True, verbose_name="Recommendation Date")

    @models.permalink
    def get_absolute_url(self):
        return ('hr.views.view_application', [self.application.id])

    @property
    def is_valid(self):
        diff = self.recommendation_date - self.user_character.corporation_date
        if self.user_character.eveaccount_set.count() and self.user_character.eveaccount_set.all()[0].api_status == API_STATUS_OK and diff.days >= settings.HR_RECOMMENDATION_DAYS and self.user_character.corporation == self.application.corporation:
            return True
        return False

    def __unicode__(self):
        return self.user_character.name


class Audit(models.Model):
    """ Auditing information regarding a application """

    application = models.ForeignKey(Application, blank=False, verbose_name="Application")
    user = models.ForeignKey(User, blank=True, verbose_name="User")
    event = models.IntegerField(choices=AUDIT_EVENT_CHOICES,
                                     verbose_name="Event Type",
                                     help_text="Type of audit event")
    text = models.TextField(blank=False, verbose_name="Event Text",
                                     help_text="Detailed event text")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Event Date")

    @models.permalink
    def get_absolute_url(self):
        return ('hr.views.view_application', [self.application.id])

    def __unicode__(self):
        return u"(%s) %s: %s" % (self.get_event_display(), self.user, self.text)


class BlacklistSource(models.Model):
    """ Blacklist Source """

    name =  models.CharField("Blacklist Source Name", max_length=255, blank=False)
    ticker = models.CharField("Blacklist Source Ticker", max_length=255, blank=False)

    def __unicode__(self):
        return self.name


class Blacklist(models.Model):
    """ Blacklisted entries, stops people who match the criteria from applying """

    type = models.IntegerField(choices=BLACKLIST_TYPE_CHOICES,
                                     verbose_name="Blacklisted Type",
                                     help_text="Type of entity to be blacklisted")
    level = models.IntegerField(choices=BLACKLIST_LEVEL_CHOICES,
                                     verbose_name="Blacklist Level",
                                     help_text="Level of blacklisting", default=BLACKLIST_LEVEL_BLACKLIST)
    value = models.CharField("Blacklisted Value", max_length=255, blank=False)
    reason = models.TextField(blank=False, verbose_name="Reason",
                                     help_text="Reason that the entity was blacklisted")
    expiry_date = models.DateTimeField(verbose_name="Expiry Date", blank=False, null=True,
                                     help_text="Date to expire this entry")
    source = models.ForeignKey(BlacklistSource, blank=False, verbose_name="Source")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Created Date")
    created_by = models.ForeignKey(User, blank=False, verbose_name="Created By")

    def __unicode__(self):
        return u'%s: %s' % (self.get_type_display(), self.value)


class ApplicationConfig(models.Model):
    """ Defines configuration settings for applications """

    corporation = models.OneToOneField(EVEPlayerCorporation, blank=False, verbose_name="Corporation", related_name="application_config")
    is_accepting = models.BooleanField(verbose_name="Accepting Applications",
                                       help_text="Defines if the corporation is accepting applications")
    api_required = models.IntegerField(choices=API_KEYTYPE_CHOICES, default=1, verbose_name="Minimum API Key Level",
                                       help_text="This defines the minimum level of API needed to create a application")
    api_view = models.BooleanField(verbose_name="View Applicant APIs",
                                       help_text="This allows HR staff to see the applicant's API keys")

    def __unicode__(self):
        return u'%s' % self.corporation

    class Meta:
        verbose_name = 'Application Config'
        verbose_name_plural = 'Application Configs'
        ordering = ['corporation']


class TemplateMessage(models.Model):
    """ A message template for communications in applications """

    config = models.ForeignKey(ApplicationConfig, related_name="templates")
    name = models.CharField("Template Name", max_length="200", blank=False, null=False)
    text = models.TextField("Text", blank=False, null=False)

    def render_template(self, values):
        return Template(self.text).render(Context(values))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'Template Message'
        verbose_name_plural = u'Template Messages'
        ordering = ['config', 'name']
