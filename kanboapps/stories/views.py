# Create your views here.

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from models import Board, Story, toposorted

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
    return {
        'boards': Board.objects.all(),
    }

@with_template('stories/story-list.html')
def story_list(request, board_id):
    board = get_object_or_404(Board, pk=board_id)

    return {
        'board': board,
        'stories': toposorted(board.story_set.all()),
    }