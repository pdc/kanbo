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
    prepopulated_fields = {"label": ("name",)}
    list_display = ['name', 'label', 'owner', 'created']

class CardAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("label",)}
    list_display = ['slug', 'label', 'succ', 'created']

admin.site.register(Board, BoardAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(Bag, BagAdmin)
#admin.site.register(Tag, TagInline)