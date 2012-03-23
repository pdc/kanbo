# -*- coding: UTF-8 -*-

"""Declarations for models used in the stories app."""

from django.db import models


class Bag(models.Model):
    name = models.SlugField(max_length=200)
    label = models.CharField(max_length=200)

    def __unicode__(self):
        return self.label


class Tag(models.Model):
    bag = models.ForeignKey(Bag)

    name = models.SlugField(max_length=200)

    def __unicode__(self):
        return u'{0}:{1}'.format(self.bag.name, self.name)


class Board(models.Model):
    """The universe of stories for one team, or group of teams."""
    label = models.CharField(max_length=200)
    slug = models.SlugField()

    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateField(auto_now=True, editable=False)

    def __unicode__(self):
        return self.label


class Story(models.Model):
    """On thing on a board"""
    board = models.ForeignKey(Board)
    tag_set = models.ManyToManyField(Tag, related_name='story_set', blank=True)

    label = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(max_length=2000, blank=True, null=True)

    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateField(auto_now=True, editable=False)

    class Meta:
        verbose_name_plural = u'stories'
        
    def __unicode__(self):
        return self.label
