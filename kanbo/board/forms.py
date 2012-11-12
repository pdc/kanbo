# -*- coding: UTF-8 -*-

import re
from django import forms
from django.forms import ModelForm
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from kanbo.board.models import Board, Bag, Tag, Card, Access

class BoardForm(ModelForm):
    class Meta:
        model = Board
        exclude = ['owner', 'collaborators']

class BagForm(ModelForm):
    class Meta:
        model = Bag
        exclude = ['board']

    initial_tags = forms.CharField(max_length=1000,
        required=False,
        widget=forms.Textarea,
        validators=[RegexValidator(re.compile(r'^[a-z\d\n-]*$', re.MULTILINE), )],
        help_text='Initial set of tag values, one per line. Tags should consist of letters, digits, and dashes only (no spaces). Tags must be unique within the scope of this bag.')

class TagForm(ModelForm):
    class Meta:
        model = Tag
        exclude = ['bag', 'succ']

class CardForm(ModelForm):
    class Meta:
        model = Card
        exclude = ['board', 'succ', 'tag_set']

def card_form_for_board(board, post_vars=None, label=None, href=None):
    """Form for creating or editing a card on this board."""
    if post_vars:
        return CardForm(post_vars, instance=Card(board=board))
    else:
        default_name = str(1 + board.card_set.count())
        default_label = label or ''
        default_href = href or ''
        return CardForm(instance=Card(board=board, name=default_name,
                label=default_label, href=default_href))

class AccessForm(ModelForm):
    class Meta:
        model = Access
        exclude = ['board']