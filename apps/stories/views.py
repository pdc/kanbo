# Create your views here.

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from models import Board

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