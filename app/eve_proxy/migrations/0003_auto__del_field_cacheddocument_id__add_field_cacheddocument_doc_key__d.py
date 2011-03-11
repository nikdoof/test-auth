# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Delete all records
        db.execute("DELETE FROM eve_proxy_cacheddocument")
        
        # Removing unique constraint on 'CachedDocument', fields ['url_path']
        db.delete_unique('eve_proxy_cacheddocument', ['url_path'])

        # Deleting field 'CachedDocument.id'
        db.delete_column('eve_proxy_cacheddocument', 'id')

        # Adding field 'CachedDocument.doc_key'
        db.add_column('eve_proxy_cacheddocument', 'doc_key', self.gf('django.db.models.fields.CharField')(default='xxx', max_length=40, primary_key=True), keep_default=False)


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'CachedDocument.id'
        raise RuntimeError("Cannot reverse this migration. 'CachedDocument.id' and its values cannot be restored.")

        # Deleting field 'CachedDocument.doc_key'
        db.delete_column('eve_proxy_cacheddocument', 'doc_key')

        # Adding unique constraint on 'CachedDocument', fields ['url_path']
        db.create_unique('eve_proxy_cacheddocument', ['url_path'])


    models = {
        'eve_proxy.apiaccesslog': {
            'Meta': {'ordering': "['time_access']", 'object_name': 'ApiAccessLog'},
            'document': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'time_access': ('django.db.models.fields.DateTimeField', [], {}),
            'userid': ('django.db.models.fields.IntegerField', [], {})
        },
        'eve_proxy.cacheddocument': {
            'Meta': {'ordering': "['time_retrieved']", 'object_name': 'CachedDocument'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'cached_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'doc_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'primary_key': 'True'}),
            'time_retrieved': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'url_path': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['eve_proxy']
