# -*- coding: UTF-8 -*-

import logging
import json
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, redirect
from models import Board, Story, Bag, Tag, toposorted, rearrange_objects

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
    return {
        'many_boards': board_count > 1,
        'board': board,
        'grid': grid,
        'col_name': col_name,
        'col_tags': [t for b in grid.rows[0].bins if b.tags for t in b.tags],
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

def rearrangement_ajax(request, board_id, col_name):
    logger.debug(request.body)
    success = process_rearrangement(request, board_id, col_name)
    res = success or {}
    res['success'] = bool(success)
    return HttpResponse(json.dumps(res), content_type="application/json")

def process_rearrangement(request, board_id, col_name):
    board = get_object_or_404(Board, pk=board_id)
    if request.method == 'POST':
        # Update dropped stories
        dropped_id = request.POST.get('dropped')
        if dropped_id:
            dropped = get_object_or_404(Story, id=dropped_id)
            axis_bag = get_object_or_404(Bag, name=col_name)
            dropped.replace_tags([axis_bag], request.POST.getlist('tags'))
            dropped.save()
        ids = [(None if x == '-' else int(x)) for s in request.POST.getlist('order') for x in s.split()]
        rearrange_objects(Story, ids)
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