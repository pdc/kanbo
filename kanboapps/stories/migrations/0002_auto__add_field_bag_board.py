# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Bag.board'
        db.add_column('stories_bag', 'board',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stories.Board'], null=True),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'Bag.board'
        db.delete_column('stories_bag', 'board_id')

    models = {
        'stories.bag': {
            'Meta': {'object_name': 'Bag'},
            'board': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stories.Board']", 'null': 'True'}),
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