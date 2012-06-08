# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        from api.urls import urlpatterns as urls
        
        for u in urls:
            if not u.name is None:
                orm['api.AuthAPIKeyPermission'].objects.get_or_create(key=u.name, name=u.name)
        perms = orm['api.AuthAPIKeyPermission'].objects.all()
        
        for key in orm['api.AuthAPIKey'].objects.all():
            key.permissions.add(*perms)


    def backwards(self, orm):
        for key in orm['api.AuthAPIKey'].objects.all():
            key.permissions.clear()
            
        orm['api.AuthAPIKeyPermission'].objects.all().delete()    

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
    symmetrical = True
