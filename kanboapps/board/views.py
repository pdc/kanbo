# -*- coding: UTF-8 -*-

import logging
import json
from django.core.exceptions import PermissionDenied, ValidationError, NON_FIELD_ERRORS
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.defaultfilters import pluralize
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from kanboapps.board.models import Board, Access, Card, Bag, Tag, toposorted, rearrange_objects, EventRepeater
from kanboapps.board.forms import BoardForm, BagForm, TagForm, card_form_for_board, CardForm, AccessForm
from kanboapps.shortcuts import with_template, returns_json

logger = logging.getLogger(__name__)

def that_owner(view_func):
    """View decorator that translates  an owner_username in to an owner."""
    def wrapped_view(request, owner_username, *args, **kwargs):
        owner = get_object_or_404(User, username=owner_username)
        result = view_func(request, owner, *args, **kwargs) or {}
        if hasattr(result, 'items'):
            result['owner'] = owner
        return result
    return wrapped_view

def that_board(view_func):
    """View decorator that translates  an owner_username in to an owner."""
    def wrapped_view(request, owner_username, board_name, *args, **kwargs):
        owner = get_object_or_404(User, username=owner_username)
        board = get_object_or_404(Board, owner=owner, name=board_name)
        result = view_func(request, owner, board, *args, **kwargs) or {}
        if hasattr(result, 'items'):
            result['owner'] = owner
            result['board'] = board
            result['allows_rearrange'] = board.allows_rearrange(request.user)
        return result
    return wrapped_view

def redirect_to_board_detail(board, view_name='board-detail'):
    return redirect(view_name,
        owner_username=board.owner.username,
        board_name=board.name)

def redirect_to_board(board, col_name=None, view_name='card-grid'):
    """Return a HttpresponseRedirect to this board.

    If col_name is specified, jump to the specified grid.
    Otherwise go to teh default page for that board
    (currently the default grid view).
    """
    if not col_name:
        col_name=board.bags[0].name
    return redirect(view_name,
        owner_username=board.owner.username,
        board_name=board.name,
        col_name=col_name)


@with_template('board/user-profile.html')
@that_owner
def user_profile(request, owner):
    boards = owner.board_set.all()
    return {
        'boards': boards,
    }

@login_required
@with_template('board/new-board.html')
@that_owner
def new_board(request, owner):
    if owner != request.user:
        messages.info(request, 'You can’t create a board in someone else’s profile.')
        return redirect('new-board', owner_username=request.user.username)
    if request.method == 'POST':
        form = BoardForm(request.POST, instance=Board(owner=owner))
        if form.is_valid():
            board = form.save()
            bag = board.bag_set.create(name='state')
            for x in ['todo', 'doing', 'done']:
                bag.tag_set.create(name=x)
            ##messages.info(request, 'Created a'.format(count, pluralize(count)))
            return redirect_to_board_detail(board)
    else:
        form = BoardForm() # An unbound form
    return {
        'form': form,
        'non_field_errors': form.errors.get(NON_FIELD_ERRORS),
    }

@with_template('board/board-detail.html')
@that_board
def board_detail(request, owner, board):
    #cards = toposorted(board.card_set.all())
    collaborators = board.collaborators.all()
    for x in collaborators:
        x.can_rearrange = board.allows_rearrange(x)
    return {
        'board': board,
        'collaborators': collaborators,
        'any_cant_rearrange': any(not x.can_rearrange for x in collaborators),
        'bags': board.bag_set.all(),
        'allows_add_remove_user': board.allows_add_remove_user(request.user),
        'add_user_form': AccessForm(instance=Access(board=board)),
    }

@with_template('board/add-user.html')
@that_board
def add_user(request, owner, board):
    if not board.allows_add_remove_user(request.user):
        messages.info(request, 'You can’t add users to this board.')
        return redirect_to_board_detail(board)

    if request.method == 'POST':
        form = AccessForm(request.POST, instance=Access(board=board))
        if form.is_valid():
            try:
                access = Access.objects.get(user=form.cleaned_data['user'], board=board)
                access.can_rearrange = form.cleaned_data['can_rearrange']
                access.save()
                messages.info(request, '{0} was already a member.'.format(access.user.username))
            except Access.DoesNotExist:
                access = form.save()
            return redirect_to_board_detail(board)
    else:
        form = AccessForm(instance=Access(board=board)) # blank form
    return {
        'form': form,
        'non_field_errors': form.errors.get(NON_FIELD_ERRORS),
    }

@with_template('board/grid.html')
@that_board
def card_grid(request, owner, board, col_name):
    col_bag = get_object_or_404(Bag, board=board, name=col_name)
    grid = board.make_grid(col_bag)

    is_polling_enabled = settings.EVENT_REPEATER.get('POLL')
    next_seq = board.event_stream().next_seq() if is_polling_enabled else None

    return {
        'board': board,
        'grid': grid,
        'col_name': col_name,
        'col_tags': [t for b in grid.rows[0].bins if b.tags for t in b.tags],
        'is_polling_enabled': is_polling_enabled,
        'next_seq': next_seq,
        'new_card_form': card_form_for_board(board),
    }

@with_template('board/grid.html')
def card_arrangement(request, board_id, col_name):
    board = get_object_or_404(Board, pk=board_id)
    if process_card_arrangement(request, board, col_name):
        if col_name:
            return redirect_to_board(board, col_name)
        else:
            return redirect_to_board_detail(board)
    return {
        'board': board,
        'cards': toposorted(board.card_set.all()),
        'order':  request.POST['order'],
    }

@returns_json
def card_arrangement_ajax(request, board_id, col_name):
    board = get_object_or_404(Board, pk=board_id)
    success = process_card_arrangement(request, board, col_name)
    res = success or {}
    res['success'] = bool(success)
    return res

def process_card_arrangement(request, board, col_name):
    """Code common to the 2 card_arrangement views."""
    # Check this user has permission.
    if not board.allows_rearrange(request.user):
        raise PermissionDenied('You cannot rearrange this board')

    event  = {
        'type': 'rearrange',
        'board': board.id,
    }
    if request.method == 'POST':
        # Update dropped cards
        dropped_id = request.POST.get('dropped')
        if dropped_id:
            dropped = get_object_or_404(Card, id=dropped_id)
            axis_bag = get_object_or_404(Bag, board=board, name=col_name)
            tag_strs = request.POST.getlist('tags')
            dropped.replace_tags([axis_bag], tag_strs)
            dropped.save()

            event.update({
                'xaxis': [axis_bag.id],
                'dropped': dropped.id,
                'tags': [int(x) for x in tag_strs],
                })
        ids = [(None if x == '-' else int(x)) for s in request.POST.getlist('order') for x in s.split()]
        rearrange_objects(board.card_set, ids)

        event['order'] = ids
        er = EventRepeater()
        er.get_stream(board.id).append(event)

        success = {
            'ids': ids,
        }
        if dropped_id:
            success['dropped'] = {
                'id': dropped_id,
                'label': dropped.label,
                'tags': [{'id': t.id, 'name': t.name, 'axis': t.bag.name} for t in dropped.tag_set.all()],
            }
            success['col_axis'] = {'id': axis_bag.id, 'name': axis_bag.name}
            success['tags'] = [request.POST.getlist('tags')]
        return success

@login_required
@with_template('board/new-card.html')
@that_board
def new_card(request, owner, board, col_name):
    if request.method == 'POST':
        form = card_form_for_board(board, request.POST)
        if form.is_valid():
            card = form.save()
            return redirect_to_board(board, col_name)
    else:
        form = card_form_for_board(board)
    return {
        'col_name': col_name,
        'form': form,
        'non_field_errors': form.errors.get(NON_FIELD_ERRORS),
    }

@login_required
@with_template('board/edit-card.html')
@that_board
def edit_card(request, owner, board, col_name, card_name):
    card = get_object_or_404(Card, board=board, name=card_name)
    if request.method == 'POST':
        form = CardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            return redirect_to_board(board, col_name)
    else:
        form = CardForm(instance=card)
    return {
        'col_name': col_name,
        'form': form,
        'non_field_errors': form.errors.get(NON_FIELD_ERRORS),
    }

@with_template('board/new-card.html')
@that_board
def create_many_cards(request, owner, board, col_name):
    text = None
    logger.debug('Method = {0!r}'.format(request.method))
    if request.method == 'POST':
        text = request.POST['cards']
        count = 0
        first_id = board.card_set.count() + 1
        for label in text.strip().split('\n'):
            name = str(first_id + count)
            logger.debug('Creating {0} {1}'.format(name, label))
            board.card_set.create(name=name, label=label)
            count += 1
        if count:
            messages.info(request, 'Added {0} card{1}'.format(count, pluralize(count)))
            return redirect_to_board(board, col_name)
        # If failed, fall through to showing form again:
    return {
        'col_name': col_name,
        'text': text,
    }

@returns_json
def events_ajax(request, board_id, start_seq):
    board = get_object_or_404(Board, pk=board_id)
    start_seq = int(start_seq)

    jevents, next_seq = board.event_stream().as_json_starting_from(start_seq)
    res = {
        'ready': True,
        'pleaseWait': settings.EVENT_REPEATER.get('INTERVAL_SECONDS', 1.5) * 1000,
        # TODO. Adapt poll interval to time between recent events.
        'next': reverse('events-ajax', kwargs={'board_id': board.id, 'start_seq': str(next_seq)}),
        'events': '*',
    }
    jres = json.dumps(res).replace('"*"', jevents)
    return jres


@with_template('board/new-bag.html')
@that_board
def new_bag(request, owner, board):
    if request.method == 'POST':
        form = BagForm(request.POST, instance=Bag(board=board))
        if form.is_valid():
            bag = form.save()
            tag_names = [x.strip() for x in form.cleaned_data['initial_tags'].split()]
            for tag_name in tag_names:
                bag.tag_set.create(name=tag_name)
            return HttpResponseRedirect(board.get_detail_url())
    else:
        form = BagForm(instance=Bag(board=board))
    return {
        'board': board,
        'form': form,
        'non_field_errors': form.errors.get(NON_FIELD_ERRORS),
    }

@with_template('board/bag-detail.html')
@that_board
def bag_detail(request, owner, board, bag_name):
    bag = get_object_or_404(Bag, board=board, name=bag_name)
    return {
        'bag': bag,
        'form': TagForm(instance=Tag(bag=bag)),
        'order': ' '.join(str(x.id) for x in bag.tags_sorted()),
    }

@with_template('board/new-tag.html')
@that_board
def new_tag(request, owner, board, bag_name):
    bag = get_object_or_404(Bag, board=board, name=bag_name)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=Tag(bag=bag))
        if form.is_valid():
            tag = form.save()
            return HttpResponseRedirect(bag.get_absolute_url())
    else:
        form = TagForm(instance=Tag(bag=bag))
    return {
        'bag': bag,
        'form': form,
        'non_field_errors': form.errors.get(NON_FIELD_ERRORS),
    }

@with_template('board/bag-detail.html')
def tag_arrangement(request, bag_id):
    bag = get_object_or_404(Bag, id=bag_id)
    if request.method == 'POST':
        if process_tag_arrangement(request, bag):
            return HttpResponseRedirect(bag.get_absolute_url())
    return {
        'bag': bag,
        'form': TagForm(instance=Tag(bag=bag)),
        'order':  request.POST['order'],
        'allows_rearrange': bag.allows_rearrange(request.user),
    }

@returns_json
def tag_arrangement_ajax(request, bag_id):
    bag = get_object_or_404(Bag, pk=bag_id)
    success = process_tag_arrangement(request, bag)
    res = success or {}
    res['success'] = bool(success)
    return res

def process_tag_arrangement(request, bag):
    """Code common to the 2 card_arrangement views."""
    # Check this user has permission.
    if not bag.allows_rearrange(request.user):
        raise PermissionDenied('You cannot arrange tags on this board')

    event  = {
        'type': 'tags-arranged',
        'board': bag.board.id,
        'bag': bag.id,
    }
    if request.method == 'POST':
        ids = [(None if x == '-' else int(x)) for s in request.POST.getlist('order') for x in s.split()]
        rearrange_objects(bag.tag_set, ids)

        event['order'] = ids
        er = EventRepeater()
        er.get_stream(bag.board.id).append(event)

        success = {
            'ids': ids,
        }
        return success
