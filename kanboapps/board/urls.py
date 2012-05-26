# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('kanboapps.board.views',
    url(r'^(?P<owner_username>[\w-]+)$', 'board_list', name='board-list'),
    url(r'^(?P<owner_username>[\w-]+)/new$', 'board_new', name='board-new'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)$', 'board_detail', name='board-detail'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/grids/(?P<col_name>[\w+]+)$', 'card_grid', name='card-grid'),
    url(r'^boards/(?P<board_id>\d+)/rearrangement$', 'rearrangement', name='rearrangement'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/grids/(?P<col_name>[\w-]+)/new$', 'new_card', name='new-card'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/grids/(?P<col_name>[\w-]+)/create$', 'create_card', name='create-card'),
    url(r'^boards/(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)/rearrangement$', 'rearrangement', name='rearrangement'),
    url(r'^boards/(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)/jarrange$', 'rearrangement_ajax', name='rearrangement-ajax'),
    url(r'^boards/(?P<board_id>\d+)/jevents/(?P<start_seq>\d+)', 'events_ajax', name='events-ajax'),
)
