# -*- coding: UTF-8 -*-

"""Specifies how models are represented inthe admin pages."""

from django.contrib import admin
from models import *

class TagInline(admin.TabularInline):
    model = Tag
    
class BagAdmin(admin.ModelAdmin):
    inlines = [
        TagInline,
    ]

class BoardAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("label",)}
    
class StoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("label",)}

admin.site.register(Board, BoardAdmin)
admin.site.register(Story, StoryAdmin)
admin.site.register(Bag, BagAdmin)
#admin.site.register(Tag, TagInline)