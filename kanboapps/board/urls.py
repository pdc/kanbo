# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('kanboapps.board.views',
    url(r'^(?P<owner_username>\w+)$', 'board_list', name='board_list'),
    url(r'^(?P<owner_username>\w+)/(?P<board_id>\d+)$', 'card_list', name='card-list'),
    url(r'^(?P<owner_username>\w+)/(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)$', 'card_grid', name='card-grid'),
    url(r'^(?P<owner_username>\w+)/(?P<board_id>\d+)/rearrangement$', 'rearrangement', name='rearrangement'),
    url(r'^(?P<owner_username>\w+)/(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)/new$', 'new_card', name='new-card'),
    url(r'^(?P<owner_username>\w+)/(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)/create$', 'create_card', name='create-card'),
    url(r'^boards/(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)/rearrangement$', 'rearrangement', name='rearrangement'),
    url(r'^boards/(?P<board_id>\d+)/grids/(?P<col_name>[\w-]+)/jarrange$', 'rearrangement_ajax', name='rearrangement-ajax'),
    url(r'^boards/(?P<board_id>\d+)/jevents/(?P<start_seq>\d+)', 'events_ajax', name='events-ajax'),
)
