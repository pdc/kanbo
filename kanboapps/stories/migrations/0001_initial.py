# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Bag'
        db.create_table('stories_bag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=200)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('stories', ['Bag'])

        # Adding model 'Tag'
        db.create_table('stories_tag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stories.Bag'])),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=200)),
        ))
        db.send_create_signal('stories', ['Tag'])

        # Adding model 'Board'
        db.create_table('stories_board', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('stories', ['Board'])

        # Adding model 'Story'
        db.create_table('stories_story', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('board', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stories.Board'])),
            ('succ', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stories.Story'], null=True, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=2000, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('stories', ['Story'])

        # Adding M2M table for field tag_set on 'Story'
        db.create_table('stories_story_tag_set', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('story', models.ForeignKey(orm['stories.story'], null=False)),
            ('tag', models.ForeignKey(orm['stories.tag'], null=False))
        ))
        db.create_unique('stories_story_tag_set', ['story_id', 'tag_id'])

    def backwards(self, orm):
        # Deleting model 'Bag'
        db.delete_table('stories_bag')

        # Deleting model 'Tag'
        db.delete_table('stories_tag')

        # Deleting model 'Board'
        db.delete_table('stories_board')

        # Deleting model 'Story'
        db.delete_table('stories_story')

        # Removing M2M table for field tag_set on 'Story'
        db.delete_table('stories_story_tag_set')

    models = {
        'stories.bag': {
            'Meta': {'object_name': 'Bag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '200'})
        },
        'stories.board': {
            'Meta': {'object_name': 'Board'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'stories.story': {
            'Meta': {'ordering': "['created']", 'object_name': 'Story'},
            'board': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stories.Board']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'succ': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stories.Story']", 'null': 'True', 'blank': 'True'}),
            'tag_set': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'story_set'", 'blank': 'True', 'to': "orm['stories.Tag']"})
        },
        'stories.tag': {
            'Meta': {'object_name': 'Tag'},
            'bag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stories.Bag']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['stories']