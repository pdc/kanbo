# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from django.conf.urls import include, url
from kanbo.board import views


# Organization of this file
#
# We start with definitions of partial URL confs for
# parts of boards, then for boards (which include the former partial confs),
# and so on and end with the main URLconf


board_patterns = [  # Will be prefixed with /USER/BOARD/
    url(r'^$', views.board_detail, name='board-detail'),
    url(r'^bags/new$', views.new_bag, name='new-bag'),
    url(r'^bags/(?P<bag_name>[\w-]+)/', include([
        url(r'^$', views.bag_detail, name='bag-detail'),
        url(r'^delete$', views.delete_bag, name='delete-bag'),
        url(r'^tags/new$', views.new_tag, name='new-tag'),
    ])),
    url(r'^grids/(?P<axes>[\w+,;=]+)/', include([
        url(r'^$', views.card_grid, name='card-grid'),
        url(r'^new$', views.new_card, name='new-card'),
        url(r'^(?P<card_name>\w+)/edit$', views.edit_card, name='edit-card'),
        url(r'^create$', views.create_many_cards, name='create-many-cards'),
    ])),
    url(r'^popup-new$', views.new_card_popup, name='new-card-popup'),
    url(r'^popup-new/(?P<card_name>[\w-]+)$', views.new_card_popup_ok, name='new-card-popup-ok'),
    url(r'^users/add$', views.add_user, name='add-user'),
]

urlpatterns = [
    url(r'^(?P<owner_username>[\w-]+)/', include([
        url(r'^$', views.user_profile, name='user-profile'),
        url(r'^new$', views.new_board, name='new-board'),
        url(r'^(?P<board_name>[\w-]+)/', include(board_patterns)),
    ])),
    url(r'^boards/(?P<board_id>\d+)/', include([
        url(r'^arrangement$', views.card_arrangement, name='card-arrangement'),
        url(r'^grids/(?P<axes>[\w+,;=]+)/arrangement$', views.card_arrangement, name='card-arrangement'),
        url(r'^grids/(?P<axes>[\w+,;=]+)/jarrange$', views.card_arrangement_ajax, name='card-arrangement-ajax'),

        url(r'^jevents/(?P<start_seq>\d+)$', views.events_ajax, name='events-ajax'),
    ])),
    url(r'^bags/(?P<bag_id>\d+)/', include([
        url(r'^arrangement$', views.tag_arrangement, name='tag-arrangement'),
        url(r'^jarrange$', views.tag_arrangement_ajax, name='tag-arrangement-ajax'),
    ])),
    url(r'^autocomplete/user$', views.autocomplete_user, name='autocomplete-user'),
]