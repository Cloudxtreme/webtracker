# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'VisitorQueue'
        db.create_table(u'wt_visitor_queue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('visitor_ip', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('referer_url', self.gf('django.db.models.fields.CharField')(default=u'', max_length=1000)),
            ('page_url', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('datetime_of_visit', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'home', ['VisitorQueue'])


    def backwards(self, orm):
        # Deleting model 'VisitorQueue'
        db.delete_table(u'wt_visitor_queue')


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
        },
        u'home.visitorqueue': {
            'Meta': {'object_name': 'VisitorQueue', 'db_table': "u'wt_visitor_queue'"},
            'datetime_of_visit': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page_url': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'referer_url': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '1000'}),
            'visitor_ip': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        }
    }

    complete_apps = ['home']