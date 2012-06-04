# -*- coding: UTF-8 -*-

from django.forms import ModelForm
from django.contrib.auth.models import User
from kanboapps.board.models import Board, Access

class BoardForm(ModelForm):
    class Meta:
        model = Board
        exclude = ['owner', 'collaborators']

class AccessForm(ModelForm):
    class Meta:
        model = Access
        exclude = ['board']