# -*- coding: UTF-8 -*-

import logging
import json
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.defaultfilters import slugify, pluralize
from django.forms import ModelForm
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.conf import settings
from django.contrib.auth.models import User
from kanboapps.board.models import Board, Card, Bag, Tag, toposorted, rearrange_objects, EventRepeater
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

@with_template('board/board-list.html')
@that_owner
def board_list(request, owner):
    boards = owner.board_set.all()
    return {
        'boards': boards,
    }

@with_template('board/board-new.html')
@that_owner
def board_new(request, owner):
    # XXX check user==owner
    class BoardForm(ModelForm):
        class Meta:
            model = Board
            exclude = ['owner']
    if request.method == 'POST':
        form = BoardForm(request.POST, instance=Board(owner=owner))
        if form.is_valid():
            board = form.save()
            bag = board.bag_set.create(name='state')
            for x in ['todo', 'doing', 'done']:
                bag.tag_set.create(name=x)
            ##messages.info(request, 'Created a'.format(count, pluralize(count)))
            return redirect('card-list', owner_username=owner.username, board_id=board.id)
    else:
        form = BoardForm() # An unbound form
    return {
        'form': form,
    }

@with_template('board/card-list.html')
@that_owner
def card_list(request, owner, board_id):
    board = get_object_or_404(Board, pk=board_id, owner=owner)
    board_count = Board.objects.filter(owner=owner).count()
    cards = toposorted(board.card_set.all())
    return {
        'many_boards': board_count > 1,
        'board': board,
        'cards': cards,
        'order': ' '.join(str(x.id) for x in cards),
        'bags': board.bag_set.all(),
    }

@with_template('board/grid.html')
@that_owner
def card_grid(request, owner, board_id, col_name):
    board_count = Board.objects.count() # XXX change to includ eonly user’s boards
    board = get_object_or_404(Board, pk=board_id)
    col_bag = get_object_or_404(Bag, board_id=board_id, name=col_name)
    grid = board.make_grid(col_bag)

    is_polling_enabled = settings.EVENT_REPEATER.get('POLL')
    next_seq = board.event_stream().next_seq() if is_polling_enabled else None
    return {
        'many_boards': board_count > 1,
        'board': board,
        'grid': grid,
        'col_name': col_name,
        'col_tags': [t for b in grid.rows[0].bins if b.tags for t in b.tags],
        'is_polling_enabled': is_polling_enabled,
        'next_seq': next_seq,
    }

@with_template('board/grid.html')
@that_owner
def rearrangement(request, owner, board_id, col_name):
    if process_rearrangement(request, board_id, col_name):
        if col_name:
            u = reverse('card-grid', kwargs={'board_id': board_id, 'col_name': col_name})
        else:
            u = reverse('card-list', kwargs={'board_id': board_id})
        return HttpResponseRedirect(u)
    return {
        'board': board,
        'cards': toposorted(board.card_set.all()),
        'order':  request.POST['order'],
    }


@returns_json
def rearrangement_ajax(request, board_id, col_name):
    logger.debug(request.body)
    success = process_rearrangement(request, board_id, col_name)
    res = success or {}
    res['success'] = bool(success)
    return res

def process_rearrangement(request, board_id, col_name):
    """Code common to the 2 rearrangement views."""
    board = get_object_or_404(Board, pk=board_id)
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

@with_template('board/new-card.html')
@that_owner
def new_card(request, owner, board_id, col_name):
    board = get_object_or_404(Board, pk=board_id)
    return {
        'board': board,
        'col_name': col_name,
    }

@with_template('board/new-card.html')
@that_owner
def create_card(request, owner, board_id, col_name):
    board = get_object_or_404(Board, pk=board_id)
    text = None
    logger.debug('Method = {0!r}'.format(request.method))
    if request.method == 'POST':
        text = request.POST['cards']
        count = 0
        for label in text.strip().split('\n'):
            slug = slugify(label)
            logger.debug('Creating {0}'.format(label))
            board.card_set.create(label=label, slug=slug)
            count += 1
        if count:
            messages.info(request, 'Added {0} task{1}'.format(count, pluralize(count)))
            return redirect(card_grid, owner_username=owner.username, board_id=board.id, col_name=col_name)
        # If failed, fall through to showing form again:
    return {
        'board': board,
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


