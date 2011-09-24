# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'AuthAPIKey.callback'
        db.add_column('api_authapikey', 'callback', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'AuthAPIKey.callback'
        db.delete_column('api_authapikey', 'callback')


    models = {
        'api.authapikey': {
            'Meta': {'object_name': 'AuthAPIKey'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'callback': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
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
