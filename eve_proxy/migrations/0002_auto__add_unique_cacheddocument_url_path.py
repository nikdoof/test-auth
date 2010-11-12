# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding unique constraint on 'CachedDocument', fields ['url_path']
        db.create_unique('eve_proxy_cacheddocument', ['url_path'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'CachedDocument', fields ['url_path']
        db.delete_unique('eve_proxy_cacheddocument', ['url_path'])


    models = {
        'eve_proxy.apiaccesslog': {
            'Meta': {'object_name': 'ApiAccessLog'},
            'document': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'time_access': ('django.db.models.fields.DateTimeField', [], {}),
            'userid': ('django.db.models.fields.IntegerField', [], {})
        },
        'eve_proxy.cacheddocument': {
            'Meta': {'object_name': 'CachedDocument'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'cached_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time_retrieved': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'url_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['eve_proxy']
