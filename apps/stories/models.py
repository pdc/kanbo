# -*- coding: UTF-8 -*-

"""Declarations for models used in the stories app."""

from django.db import models

# Create your models here.
class Board(models.Model):
    """The universe of stories for one team, or group of teams."""
    label = models.CharField(max_length=200)
    slug = models.SlugField()
    
    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateField(auto_now=True, editable=False)
    
    def __unicode__(self):
        return self.label