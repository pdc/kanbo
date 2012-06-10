# -*- coding: UTF-8 -*-

from django.forms import ModelForm
from django.contrib.auth.models import User
from kanboapps.board.models import Board, Card, Access

class BoardForm(ModelForm):
    class Meta:
        model = Board
        exclude = ['owner', 'collaborators']

class CardForm(ModelForm):
    class Meta:
        model = Card
        exclude = ['board', 'succ', 'tag_set']

def card_form_for_board(board, post_vars=None):
    """Form for creating or editing a card on this board."""
    if post_vars:
        return CardForm(post_vars, instance=Card(board=board))
    else:
        default_name = str(1 + board.card_set.count())
        return CardForm(instance=Card(board=board, name=default_name))

class AccessForm(ModelForm):
    class Meta:
        model = Access
        exclude = ['board']