# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
# from django.core.management import call_command


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'QueueLock'
        db.create_table(u'wt_queue_lock', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lock_on', self.gf('django.db.models.fields.BooleanField')()),
        ))
        db.send_create_signal(u'home', ['QueueLock'])

        #initialize the table:
        # call_command("loaddata", "queue_lock.json")
        # ql = orm.QueueLock
        # ql.lock_on = False
        # ql.save()



    def backwards(self, orm):
        # Deleting model 'QueueLock'
        db.delete_table(u'wt_queue_lock')


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
        u'home.queuelock': {
            'Meta': {'object_name': 'QueueLock', 'db_table': "u'wt_queue_lock'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lock_on': ('django.db.models.fields.BooleanField', [], {})
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