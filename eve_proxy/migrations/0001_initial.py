# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'CachedDocument'
        db.create_table('eve_proxy_cacheddocument', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url_path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('time_retrieved', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('cached_until', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('eve_proxy', ['CachedDocument'])

        # Adding model 'ApiAccessLog'
        db.create_table('eve_proxy_apiaccesslog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('userid', self.gf('django.db.models.fields.IntegerField')()),
            ('service', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('time_access', self.gf('django.db.models.fields.DateTimeField')()),
            ('document', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('eve_proxy', ['ApiAccessLog'])


    def backwards(self, orm):
        
        # Deleting model 'CachedDocument'
        db.delete_table('eve_proxy_cacheddocument')

        # Deleting model 'ApiAccessLog'
        db.delete_table('eve_proxy_apiaccesslog')


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
            'url_path': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['eve_proxy']
