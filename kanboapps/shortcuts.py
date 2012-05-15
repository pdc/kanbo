# -*- coding: UTF-8 -*-

import json
from django.http import HttpResponse
from django.template import RequestContext
from django.contrib import messages
from django.shortcuts import render_to_response

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