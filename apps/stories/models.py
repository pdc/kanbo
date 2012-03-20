# -*- coding: UTF-8 -*-

"""Declarations for models used in the stories app."""

from django.db import models


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
    
    label = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(max_length=2000, blank=True, null=True)
    
    
    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateField(auto_now=True, editable=False)
    
    class Meta:
        ordering = ["created"] # change to sequence later?
        verbose_name_plural = "stories"
        
    def __unicode__(self):
        return self.label
    