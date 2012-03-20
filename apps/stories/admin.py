# -*- coding: UTF-8 -*-

"""Specifies how models are represented inthe admin pages."""

from django.contrib import admin
import models

class BoardAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("label",)}

admin.site.register(models.Board, BoardAdmin)