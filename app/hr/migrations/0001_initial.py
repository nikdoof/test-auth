# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Application'
        db.create_table('hr_application', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('character', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eve_api.EVEPlayerCharacter'])),
            ('corporation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eve_api.EVEPlayerCorporation'])),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('hr', ['Application'])

        # Adding model 'Recommendation'
        db.create_table('hr_recommendation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('user_character', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eve_api.EVEPlayerCharacter'])),
            ('application', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hr.Application'])),
        ))
        db.send_create_signal('hr', ['Recommendation'])

        # Adding model 'Audit'
        db.create_table('hr_audit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('application', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hr.Application'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], blank=True)),
            ('event', self.gf('django.db.models.fields.IntegerField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('hr', ['Audit'])

        # Adding model 'Blacklist'
        db.create_table('hr_blacklist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('reason', self.gf('django.db.models.fields.TextField')()),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('hr', ['Blacklist'])


    def backwards(self, orm):
        
        # Deleting model 'Application'
        db.delete_table('hr_application')

        # Deleting model 'Recommendation'
        db.delete_table('hr_recommendation')

        # Deleting model 'Audit'
        db.delete_table('hr_audit')

        # Deleting model 'Blacklist'
        db.delete_table('hr_blacklist')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
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
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'eve_api.eveplayeralliance': {
            'Meta': {'object_name': 'EVEPlayerAlliance'},
            'api_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_founded': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'ticker': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'})
        },
        'eve_api.eveplayercharacter': {
            'Meta': {'object_name': 'EVEPlayerCharacter'},
            'api_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'attrib_charisma': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'attrib_intelligence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'attrib_memory': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'attrib_perception': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'attrib_willpower': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'balance': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'corporation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCorporation']", 'null': 'True', 'blank': 'True'}),
            'current_location_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'director_update': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'gender': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_logoff': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'race': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'total_sp': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'eve_api.eveplayercorporation': {
            'Meta': {'object_name': 'EVEPlayerCorporation'},
            'alliance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerAlliance']", 'null': 'True', 'blank': 'True'}),
            'alliance_join_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'api_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'applications': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'ceo_character': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCharacter']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo_color1': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'logo_color2': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'logo_color3': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'logo_graphic_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'logo_shape1': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'logo_shape2': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'logo_shape3': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'member_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'shares': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'tax_rate': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'ticker': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'hr.application': {
            'Meta': {'object_name': 'Application'},
            'character': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCharacter']"}),
            'corporation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCorporation']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'hr.audit': {
            'Meta': {'object_name': 'Audit'},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hr.Application']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'blank': 'True'})
        },
        'hr.blacklist': {
            'Meta': {'object_name': 'Blacklist'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reason': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'hr.recommendation': {
            'Meta': {'object_name': 'Recommendation'},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hr.Application']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user_character': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCharacter']"})
        }
    }

    complete_apps = ['hr']
