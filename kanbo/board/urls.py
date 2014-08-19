# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from django.conf.urls import include, url
import kanbo.board.views


# Organization of this file
#
# We start with definitions of partial URL confs for
# parts of boards, then for boards (which include the former partial confs),
# and so on and end with the main URLconf


board_patterns = [  # Will be prefixed with /USER/BOARD/
    url(r'^$', kanbo.board.views.board_detail, name='board-detail'),
    url(r'^bags/new$', kanbo.board.views.new_bag, name='new-bag'),
    url(r'^bags/(?P<bag_name>[\w-]+)/', include([
        url(r'^$', kanbo.board.views.bag_detail, name='bag-detail'),
        url(r'^delete$', kanbo.board.views.delete_bag, name='delete-bag'),
        url(r'^tags/new$', kanbo.board.views.new_tag, name='new-tag'),
    ])),
    url(r'^grids/(?P<axes>[\w+,;=]+)/', include([
        url(r'^$', kanbo.board.views.card_grid, name='card-grid'),
        url(r'^new$', kanbo.board.views.new_card, name='new-card'),
        url(r'^(?P<card_name>\w+)/edit$', kanbo.board.views.edit_card, name='edit-card'),
        url(r'^create$', kanbo.board.views.create_many_cards, name='create-many-cards'),
    ])),
    url(r'^popup-new$', kanbo.board.views.new_card_popup, name='new-card-popup'),
    url(r'^popup-new/(?P<card_name>[\w-]+)$', kanbo.board.views.new_card_popup_ok, name='new-card-popup-ok'),
    url(r'^users/add$', kanbo.board.views.add_user, name='add-user'),
]

urlpatterns = [
    url(r'^(?P<owner_username>[\w-]+)/', include([
        url(r'^$', kanbo.board.views.user_profile, name='user-profile'),
        url(r'^new$', kanbo.board.views.new_board, name='new-board'),
        url(r'^(?P<board_name>[\w-]+)/', include(board_patterns)),
    ])),
    url(r'^boards/(?P<board_id>\d+)/', include([
        url(r'^arrangement$', kanbo.board.views.card_arrangement, name='card-arrangement'),
        url(r'^grids/(?P<axes>[\w+,;=]+)/arrangement$', kanbo.board.views.card_arrangement, name='card-arrangement'),
        url(r'^grids/(?P<axes>[\w+,;=]+)/jarrange$', kanbo.board.views.card_arrangement_ajax, name='card-arrangement-ajax'),

        url(r'^jevents/(?P<start_seq>\d+)$', kanbo.board.views.events_ajax, name='events-ajax'),
    ])),
    url(r'^bags/(?P<bag_id>\d+)/', include([
        url(r'^arrangement$', kanbo.board.views.tag_arrangement, name='tag-arrangement'),
        url(r'^jarrange$', kanbo.board.views.tag_arrangement_ajax, name='tag-arrangement-ajax'),
    ])),
]