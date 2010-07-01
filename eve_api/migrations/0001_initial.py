# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'EVEAccount'
        db.create_table('eve_api_eveaccount', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('api_last_updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('api_user_id', self.gf('django.db.models.fields.IntegerField')()),
            ('api_status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('eve_api', ['EVEAccount'])

        # Adding M2M table for field characters on 'EVEAccount'
        db.create_table('eve_api_eveaccount_characters', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('eveaccount', models.ForeignKey(orm['eve_api.eveaccount'], null=False)),
            ('eveplayercharacter', models.ForeignKey(orm['eve_api.eveplayercharacter'], null=False))
        ))
        db.create_unique('eve_api_eveaccount_characters', ['eveaccount_id', 'eveplayercharacter_id'])

        # Adding model 'EVEPlayerCharacter'
        db.create_table('eve_api_eveplayercharacter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('api_last_updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('corporation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eve_api.EVEPlayerCorporation'], null=True, blank=True)),
            ('race', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('balance', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('attrib_intelligence', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('attrib_memory', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('attrib_charisma', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('attrib_perception', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('attrib_willpower', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('total_sp', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('current_location_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_logoff', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('director_update', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('eve_api', ['EVEPlayerCharacter'])

        # Adding model 'EVEPlayerAlliance'
        db.create_table('eve_api_eveplayeralliance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('api_last_updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('ticker', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
            ('member_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('date_founded', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True, blank=True)),
        ))
        db.send_create_signal('eve_api', ['EVEPlayerAlliance'])

        # Adding model 'EVEPlayerCorporation'
        db.create_table('eve_api_eveplayercorporation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('api_last_updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ticker', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('ceo_character', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eve_api.EVEPlayerCharacter'], null=True, blank=True)),
            ('alliance', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eve_api.EVEPlayerAlliance'], null=True, blank=True)),
            ('alliance_join_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('tax_rate', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('member_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('shares', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('logo_graphic_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('logo_shape1', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('logo_shape2', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('logo_shape3', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('logo_color1', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('logo_color2', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('logo_color3', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'], null=True, blank=True)),
            ('applications', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('eve_api', ['EVEPlayerCorporation'])


    def backwards(self, orm):
        
        # Deleting model 'EVEAccount'
        db.delete_table('eve_api_eveaccount')

        # Removing M2M table for field characters on 'EVEAccount'
        db.delete_table('eve_api_eveaccount_characters')

        # Deleting model 'EVEPlayerCharacter'
        db.delete_table('eve_api_eveplayercharacter')

        # Deleting model 'EVEPlayerAlliance'
        db.delete_table('eve_api_eveplayeralliance')

        # Deleting model 'EVEPlayerCorporation'
        db.delete_table('eve_api_eveplayercorporation')


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
        'eve_api.eveaccount': {
            'Meta': {'object_name': 'EVEAccount'},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'api_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'api_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'api_user_id': ('django.db.models.fields.IntegerField', [], {}),
            'characters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['eve_api.EVEPlayerCharacter']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
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
        }
    }

    complete_apps = ['eve_api']
