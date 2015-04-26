# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Organization'
        db.create_table(u'wt_organization', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('organization_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('organization_address', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=2)),
        ))
        db.send_create_signal(u'home', ['Organization'])

        # Adding unique constraint on 'Organization', fields ['country', 'organization_name']
        db.create_unique(u'wt_organization', ['country', 'organization_name'])

        # Adding model 'Ip'
        db.create_table(u'wt_ip', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['home.Organization'], null=True)),
            ('ip_address', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal(u'home', ['Ip'])

        # Adding unique constraint on 'Ip', fields ['organization', 'ip_address']
        db.create_unique(u'wt_ip', ['organization_id', 'ip_address'])

        # Adding model 'Visitor'
        db.create_table(u'wt_visitor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('referer_url', self.gf('django.db.models.fields.CharField')(default=u'', max_length=1000)),
            ('page_url', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('datetime_of_visit', self.gf('django.db.models.fields.DateTimeField')()),
            ('ip', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['home.Ip'])),
        ))
        db.send_create_signal(u'home', ['Visitor'])


    def backwards(self, orm):
        # Removing unique constraint on 'Ip', fields ['organization', 'ip_address']
        db.delete_unique(u'wt_ip', ['organization_id', 'ip_address'])

        # Removing unique constraint on 'Organization', fields ['country', 'organization_name']
        db.delete_unique(u'wt_organization', ['country', 'organization_name'])

        # Deleting model 'Organization'
        db.delete_table(u'wt_organization')

        # Deleting model 'Ip'
        db.delete_table(u'wt_ip')

        # Deleting model 'Visitor'
        db.delete_table(u'wt_visitor')


    models = {
        u'home.ip': {
            'Meta': {'unique_together': "((u'organization', u'ip_address'),)", 'object_name': 'Ip', 'db_table': "u'wt_ip'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['home.Organization']", 'null': 'True'})
        },
        u'home.organization': {
            'Meta': {'unique_together': "((u'country', u'organization_name'),)", 'object_name': 'Organization', 'db_table': "u'wt_organization'"},
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization_address': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'organization_name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'home.visitor': {
            'Meta': {'object_name': 'Visitor', 'db_table': "u'wt_visitor'"},
            'datetime_of_visit': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['home.Ip']"}),
            'page_url': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'referer_url': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '1000'})
        }
    }

    complete_apps = ['home']