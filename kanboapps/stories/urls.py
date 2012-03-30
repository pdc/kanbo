# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('kanboapps.stories.views',
    url(r'^$', 'board_list', name='board_list'),
    url(r'^(?P<board_id>\d+)$', 'story_list', name='story-list'),
    url(r'^(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)$', 'story_grid', name='story-grid'),
    url(r'^(?P<board_id>\d+)/rearrangement$', 'rearrangement', name='rearrangement'),
    url(r'^(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)/rearrangement$', 'rearrangement', name='rearrangement'),
    url(r'^(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)/rearrangement\.json$', 'rearrangement_ajax', name='rearrangement-ajax'),
)
