# -*- coding: UTF-8 -*-

import logging
import json
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.defaultfilters import slugify, pluralize
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404, redirect
from models import Board, Story, Bag, Tag, toposorted, rearrange_objects, EventRepeater

logger = logging.getLogger(__name__)

def with_template(template_name):
    """Decorator for view functions.

    The wrapped function returns a dictionary
    that is used as template arguments."""
    def decorator(view):
        def decorated_view(request, *args, **kwargs):
            response = view(request, *args, **kwargs)
            if isinstance(response, HttpResponse):
                return response
            template_args = response or {}
            return render_to_response(template_name, template_args,
                    context_instance=RequestContext(request))
        return decorated_view
    return decorator

def returns_json(func):
    """Decorator for view fiunctions that return JSON."""
    def wrapped_func(request, *args, **kwargs):
        res = func(request, *args, **kwargs)
        if isinstance(res, basestring):
            jres = res
        else:
            jres = json.dumps(res)
        return HttpResponse(jres, content_type="application/json")
    return wrapped_func


@with_template('stories/board-list.html')
def board_list(request):
    # XXX change the following to only list current user’s boards
    boards = Board.objects.all()
    if len(boards) == 1:
        return redirect(story_list, board_id=boards[0].id)

    return {
        'boards': boards,
    }

@with_template('stories/story-list.html')
def story_list(request, board_id):
    board_count = Board.objects.count() # XXX change to includ eonly user’s boards
    board = get_object_or_404(Board, pk=board_id)
    stories = toposorted(board.story_set.all())
    return {
        'many_boards': board_count > 1,
        'board': board,
        'stories': stories,
        'order': ' '.join(str(x.id) for x in stories),
        'bags': board.bag_set.all(),
    }

@with_template('stories/story-grid.html')
def story_grid(request, board_id, col_name):
    board_count = Board.objects.count() # XXX change to includ eonly user’s boards
    board = get_object_or_404(Board, pk=board_id)
    col_bag = get_object_or_404(Bag, board_id=board_id, name=col_name)
    grid = board.make_grid(col_bag)
    next_seq = board.event_stream().next_seq()
    return {
        'many_boards': board_count > 1,
        'board': board,
        'grid': grid,
        'col_name': col_name,
        'col_tags': [t for b in grid.rows[0].bins if b.tags for t in b.tags],
        'next_seq': next_seq,
    }

@with_template('stories/story-list.html')
def rearrangement(request, board_id, col_name):
    if process_rearrangement(request, board_id, col_name):
        if col_name:
            u = reverse('story-grid', kwargs={'board_id': board_id, 'col_name': col_name})
        else:
            u = reverse('story-list', kwargs={'board_id': board_id})
        return HttpResponseRedirect(u)
    return {
        'board': board,
        'stories': toposorted(board.story_set.all()),
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
        # Update dropped stories
        dropped_id = request.POST.get('dropped')
        if dropped_id:
            dropped = get_object_or_404(Story, id=dropped_id)
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
        rearrange_objects(Story, ids)

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

@with_template('stories/new-story.html')
def new_story(request, board_id, col_name):
    board = get_object_or_404(Board, pk=board_id)
    return {
        'board': board,
        'col_name': col_name,
    }

@with_template('stories/new-story.html')
def create_story(request, board_id, col_name):
    board = get_object_or_404(Board, pk=board_id)
    text = None
    logger.debug('Method = {0!r}'.format(request.method))
    if request.method == 'POST':
        text = request.POST['stories']
        count = 0
        for label in text.strip().split('\n'):
            slug = slugify(label)
            logger.debug('Creating {0}'.format(label))
            board.story_set.create(label=label, slug=slug)
            count += 1
        if count:
            messages.info(request, 'Added {0} task{1}'.format(count, pluralize(count)))
            return redirect(story_grid, board_id=board.id, col_name=col_name)
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
        'pleaseWait': 15000 / (next_seq - start_seq) if next_seq > start_seq else 30000,
        'next': reverse('events-ajax', kwargs={'board_id': board.id, 'start_seq': str(next_seq)}),
        'events': '*',
    }
    jres = json.dumps(res).replace('"*"', jevents)
    return jres


