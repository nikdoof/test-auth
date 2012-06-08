# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AuthAPIKeyPermission'
        db.create_table('api_authapikeypermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('api', ['AuthAPIKeyPermission'])

        # Adding M2M table for field permissions on 'AuthAPIKey'
        db.create_table('api_authapikey_permissions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('authapikey', models.ForeignKey(orm['api.authapikey'], null=False)),
            ('authapikeypermission', models.ForeignKey(orm['api.authapikeypermission'], null=False))
        ))
        db.create_unique('api_authapikey_permissions', ['authapikey_id', 'authapikeypermission_id'])

    def backwards(self, orm):
        # Deleting model 'AuthAPIKeyPermission'
        db.delete_table('api_authapikeypermission')

        # Removing M2M table for field permissions on 'AuthAPIKey'
        db.delete_table('api_authapikey_permissions')

    models = {
        'api.authapikey': {
            'Meta': {'object_name': 'AuthAPIKey'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'callback': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'keys'", 'symmetrical': 'False', 'to': "orm['api.AuthAPIKeyPermission']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'api.authapikeypermission': {
            'Meta': {'object_name': 'AuthAPIKeyPermission'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'api.authapilog': {
            'Meta': {'ordering': "['access_datetime']", 'object_name': 'AuthAPILog'},
            'access_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['api.AuthAPIKey']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['api']