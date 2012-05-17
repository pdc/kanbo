# -*- coding: UTF-8 -*-

import logging
import json
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.defaultfilters import slugify, pluralize
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.conf import settings
from kanboapps.board.models import Board, Card, Bag, Tag, toposorted, rearrange_objects, EventRepeater
from kanboapps.shortcuts import with_template, returns_json

logger = logging.getLogger(__name__)

@with_template('board/board-list.html')
def board_list(request, login):
    # XXX change the following to only list current user’s boards
    boards = Board.objects.all()
    if len(boards) == 1:
        return redirect(card_list, board_id=boards[0].id)

    return {
        'boards': boards,
    }

@with_template('board/card-list.html')
def card_list(request, login, board_id):
    board_count = Board.objects.count() # XXX change to includ eonly user’s boards
    board = get_object_or_404(Board, pk=board_id)
    cards = toposorted(board.card_set.all())
    return {
        'many_boards': board_count > 1,
        'board': board,
        'cards': cards,
        'order': ' '.join(str(x.id) for x in cards),
        'bags': board.bag_set.all(),
    }

@with_template('board/grid.html')
def card_grid(request, login, board_id, col_name):
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
def rearrangement(request, login, board_id, col_name):
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
            axis_bag = get_object_or_404(Bag, name=col_name)
            tag_strs = request.POST.getlist('tags')
            dropped.replace_tags([axis_bag], tag_strs)
            dropped.save()

            event.update({
                'xaxis': [axis_bag.id],
                'dropped': dropped.id,
                'tags': [int(x) for x in tag_strs],
                })
        ids = [(None if x == '-' else int(x)) for s in request.POST.getlist('order') for x in s.split()]
        rearrange_objects(Card, ids)

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
def new_card(request, login, board_id, col_name):
    board = get_object_or_404(Board, pk=board_id)
    return {
        'board': board,
        'col_name': col_name,
    }

@with_template('board/new-card.html')
def create_card(request, login, board_id, col_name):
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
            return redirect(card_grid, board_id=board.id, col_name=col_name)
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


