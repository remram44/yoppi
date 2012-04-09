# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FtpServer'
        db.create_table('ftp_ftpserver', (
            ('address', self.gf('django.db.models.fields.CharField')(max_length=200, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=30, blank=True)),
            ('online', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('size', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('last_online', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 4, 9, 0, 0))),
            ('indexing', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('ftp', ['FtpServer'])

        # Adding model 'File'
        db.create_table('ftp_file', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('server', self.gf('django.db.models.fields.related.ForeignKey')(related_name='files', to=orm['ftp.FtpServer'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
            ('is_directory', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('size', self.gf('django.db.models.fields.IntegerField')()),
            ('old', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('ftp', ['File'])

    def backwards(self, orm):
        # Deleting model 'FtpServer'
        db.delete_table('ftp_ftpserver')

        # Deleting model 'File'
        db.delete_table('ftp_file')

    models = {
        'ftp.file': {
            'Meta': {'object_name': 'File'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_directory': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'old': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['ftp.FtpServer']"}),
            'size': ('django.db.models.fields.IntegerField', [], {})
        },
        'ftp.ftpserver': {
            'Meta': {'object_name': 'FtpServer'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'}),
            'indexing': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'last_online': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 9, 0, 0)'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30', 'blank': 'True'}),
            'online': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['ftp']