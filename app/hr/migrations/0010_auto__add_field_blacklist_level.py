# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Blacklist.level'
        db.add_column('hr_blacklist', 'level', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Blacklist.level'
        db.delete_column('hr_blacklist', 'level')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'eve_api.eveplayeralliance': {
            'Meta': {'ordering': "['date_founded']", 'object_name': 'EVEPlayerAlliance'},
            'api_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_founded': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'executor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCorporation']", 'null': 'True', 'blank': 'True'}),
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
            'corporation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'current_location_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_logoff': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'race': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['eve_api.EVEPlayerCharacterRole']", 'null': 'True', 'blank': 'True'}),
            'security_status': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'skills': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['eve_api.EVESkill']", 'through': "orm['eve_api.EVEPlayerCharacterSkill']", 'symmetrical': 'False'}),
            'total_sp': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'eve_api.eveplayercharacterrole': {
            'Meta': {'object_name': 'EVEPlayerCharacterRole'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'roleid': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'eve_api.eveplayercharacterskill': {
            'Meta': {'object_name': 'EVEPlayerCharacterSkill'},
            'character': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCharacter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_training': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'skill': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVESkill']"}),
            'skillpoints': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'eve_api.eveplayercorporation': {
            'Meta': {'object_name': 'EVEPlayerCorporation'},
            'alliance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerAlliance']", 'null': 'True', 'blank': 'True'}),
            'alliance_join_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'api_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
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
        'eve_api.eveskill': {
            'Meta': {'object_name': 'EVESkill'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVESkillGroup']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'eve_api.eveskillgroup': {
            'Meta': {'object_name': 'EVESkillGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'hr.application': {
            'Meta': {'object_name': 'Application'},
            'application_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'character': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCharacter']"}),
            'corporation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCorporation']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'hr.applicationconfig': {
            'Meta': {'ordering': "['corporation']", 'object_name': 'ApplicationConfig'},
            'api_required': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'api_view': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'corporation': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'application_config'", 'unique': 'True', 'to': "orm['eve_api.EVEPlayerCorporation']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_accepting': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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
            'expiry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'reason': ('django.db.models.fields.TextField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hr.BlacklistSource']"}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'hr.blacklistsource': {
            'Meta': {'object_name': 'BlacklistSource'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ticker': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'hr.recommendation': {
            'Meta': {'object_name': 'Recommendation'},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hr.Application']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recommendation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user_character': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eve_api.EVEPlayerCharacter']"})
        }
    }

    complete_apps = ['hr']
