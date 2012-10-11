# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'IndexerParameter'
        db.create_table('indexer_indexerparameter', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20, primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('indexer', ['IndexerParameter'])


    def backwards(self, orm):
        # Deleting model 'IndexerParameter'
        db.delete_table('indexer_indexerparameter')


    models = {
        'indexer.indexerparameter': {
            'Meta': {'object_name': 'IndexerParameter'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['indexer']