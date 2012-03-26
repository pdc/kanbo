# -*- coding: UTF-8 -*-

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, redirect
from models import Board, Story, toposorted, rearrange_objects

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
    }

@with_template('stories/story-list.html')
def rearrangement(request, board_id):
    board = get_object_or_404(Board, pk=board_id)
    if request.method == 'POST':
        ids = [(None if x == '-' else int(x)) for x in request.POST['order'].split()]
        rearrange_objects(Story, ids)
        return HttpResponseRedirect(reverse('story-list', kwargs={'board_id': board_id}))

    return {
        'board': board,
        'stories': toposorted(board.story_set.all()),
        'order':  request.POST['order'],
    }