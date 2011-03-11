# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'AuthAPIKey'
        db.create_table('api_authapikey', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('api', ['AuthAPIKey'])

        # Adding model 'AuthAPILog'
        db.create_table('api_authapilog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('access_datetime', self.gf('django.db.models.fields.DateTimeField')()),
            ('key', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['api.AuthAPIKey'])),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('api', ['AuthAPILog'])


    def backwards(self, orm):
        
        # Deleting model 'AuthAPIKey'
        db.delete_table('api_authapikey')

        # Deleting model 'AuthAPILog'
        db.delete_table('api_authapilog')


    models = {
        'api.authapikey': {
            'Meta': {'object_name': 'AuthAPIKey'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'api.authapilog': {
            'Meta': {'object_name': 'AuthAPILog'},
            'access_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['api.AuthAPIKey']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['api']
