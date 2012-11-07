# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Board'
        db.create_table('board_board', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('board', ['Board'])

        # Adding model 'Bag'
        db.create_table('board_bag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('board', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['board.Board'], null=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=200)),
        ))
        db.send_create_signal('board', ['Bag'])

        # Adding model 'Tag'
        db.create_table('board_tag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['board.Bag'])),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=200)),
        ))
        db.send_create_signal('board', ['Tag'])

        # Adding model 'Card'
        db.create_table('board_card', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('board', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['board.Board'])),
            ('succ', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['board.Card'], null=True, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('board', ['Card'])

        # Adding M2M table for field tag_set on 'Card'
        db.create_table('board_card_tag_set', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('card', models.ForeignKey(orm['board.card'], null=False)),
            ('tag', models.ForeignKey(orm['board.tag'], null=False))
        ))
        db.create_unique('board_card_tag_set', ['card_id', 'tag_id'])

    def backwards(self, orm):
        # Deleting model 'Board'
        db.delete_table('board_board')

        # Deleting model 'Bag'
        db.delete_table('board_bag')

        # Deleting model 'Tag'
        db.delete_table('board_tag')

        # Deleting model 'Card'
        db.delete_table('board_card')

        # Removing M2M table for field tag_set on 'Card'
        db.delete_table('board_card_tag_set')

    models = {
        'board.bag': {
            'Meta': {'object_name': 'Bag'},
            'board': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['board.Board']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '200'})
        },
        'board.board': {
            'Meta': {'object_name': 'Board'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'board.card': {
            'Meta': {'ordering': "['created']", 'object_name': 'Card'},
            'board': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['board.Board']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'succ': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['board.Card']", 'null': 'True', 'blank': 'True'}),
            'tag_set': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'card_set'", 'blank': 'True', 'to': "orm['board.Tag']"})
        },
        'board.tag': {
            'Meta': {'ordering': "['id']", 'object_name': 'Tag'},
            'bag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['board.Bag']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['board']