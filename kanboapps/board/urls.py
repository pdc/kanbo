# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('kanboapps.board.views',
    url(r'^(?P<owner_username>[\w-]+)$', 'user_profile', name='user-profile'),
    url(r'^(?P<owner_username>[\w-]+)/new$', 'new_board', name='new-board'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)$', 'board_detail', name='board-detail'),

    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/bags/new$', 'new_bag', name='new-bag'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/bags/(?P<bag_name>[\w-]+)$', 'bag_detail', name='bag-detail'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/bags/(?P<bag_name>[\w-]+)/delete$', 'delete_bag', name='delete-bag'),

    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/bags/(?P<bag_name>[\w-]+)/tags/new$', 'new_tag', name='new-tag'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/grids/(?P<axes>[\w+,]+)$', 'card_grid', name='card-grid'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/grids/(?P<axes>[\w+,-]+)/new$', 'new_card', name='new-card'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/grids/(?P<axes>[\w+,-]+)/(?P<card_name>\w+)/edit$', 'edit_card', name='edit-card'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/grids/(?P<axes>[\w+,-]+)/create$', 'create_many_cards', name='create-many-cards'),
    url(r'^(?P<owner_username>[\w-]+)/(?P<board_name>[\w-]+)/users/add$', 'add_user', name='add-user'),

    url(r'^boards/(?P<board_id>\d+)/arrangement$', 'card_arrangement', name='card-arrangement'),
    url(r'^boards/(?P<board_id>\d+)/grids/(?P<axes>[\w+,-]+)/arrangement$', 'card_arrangement', name='card-arrangement'),
    url(r'^boards/(?P<board_id>\d+)/grids/(?P<axes>[\w+,-]+)/jarrange$', 'card_arrangement_ajax', name='card-arrangement-ajax'),

    url('^bags/(?P<bag_id>\d+)/arrangement$', 'tag_arrangement', name='tag-arrangement'),
    url('^bags/(?P<bag_id>\d+)/jarrange$', 'tag_arrangement_ajax', name='tag-arrangement-ajax'),

    url(r'^boards/(?P<board_id>\d+)/jevents/(?P<start_seq>\d+)', 'events_ajax', name='events-ajax'),
)
