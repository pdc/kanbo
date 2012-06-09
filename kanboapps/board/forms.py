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

class AccessForm(ModelForm):
    class Meta:
        model = Access
        exclude = ['board']