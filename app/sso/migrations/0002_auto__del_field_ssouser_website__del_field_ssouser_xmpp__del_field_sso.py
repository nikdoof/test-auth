# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'SSOUser.website'
        db.delete_column('sso_ssouser', 'website')

        # Deleting field 'SSOUser.xmpp'
        db.delete_column('sso_ssouser', 'xmpp')

        # Deleting field 'SSOUser.default_service_username'
        db.delete_column('sso_ssouser', 'default_service_username')

        # Deleting field 'SSOUser.aim'
        db.delete_column('sso_ssouser', 'aim')

        # Deleting field 'SSOUser.msn'
        db.delete_column('sso_ssouser', 'msn')

        # Deleting field 'SSOUser.default_service_passwd'
        db.delete_column('sso_ssouser', 'default_service_passwd')

        # Deleting field 'SSOUser.icq'
        db.delete_column('sso_ssouser', 'icq')

        # Adding field 'SSOUser.api_service_password'
        db.add_column('sso_ssouser', 'api_service_password', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'SSOUser.website'
        db.add_column('sso_ssouser', 'website', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'SSOUser.xmpp'
        db.add_column('sso_ssouser', 'xmpp', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'SSOUser.default_service_username'
        db.add_column('sso_ssouser', 'default_service_username', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'SSOUser.aim'
        db.add_column('sso_ssouser', 'aim', self.gf('django.db.models.fields.CharField')(default='', max_length=64, blank=True), keep_default=False)

        # Adding field 'SSOUser.msn'
        db.add_column('sso_ssouser', 'msn', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'SSOUser.default_service_passwd'
        db.add_column('sso_ssouser', 'default_service_passwd', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'SSOUser.icq'
        db.add_column('sso_ssouser', 'icq', self.gf('django.db.models.fields.CharField')(default='', max_length=15, blank=True), keep_default=False)

        # Deleting field 'SSOUser.api_service_password'
        db.delete_column('sso_ssouser', 'api_service_password')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sso.service': {
            'Meta': {'object_name': 'Service'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'api': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'settings_json': ('jsonfield.fields.JSONField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'sso.serviceaccount': {
            'Meta': {'object_name': 'ServiceAccount'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sso.Service']"}),
            'service_uid': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sso.ssouser': {
            'Meta': {'object_name': 'SSOUser'},
            'api_service_password': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['sso']
