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
from django.contrib.auth import logout
from kanboapps.board.models import Board
from kanboapps.shortcuts import with_template, returns_json

def redirect_to_next(request):
    next = request.GET.get('next') or request.META.get('HTTP_REFERER')
    if next and 'hello' in next:
        next = None
    if next:
        return HttpResponseRedirect(next)
    return redirect('home')


@with_template('hello/login-form.html')
def login_form(request):
    return {}

def logged_in(request):
    return redirect_to_next(request)

def log_out(request):
    logout(request)
    return redirect_to_next(request)


@with_template('hello/login-form.html')
def login_error(request):
    return {}

@with_template('hello/login-form.html')
def create_user(request):
    return {}

@with_template('hello/login-form.html')
def create_association(request):
    if request.user.is_authenticated():
        boards = Board.objects.all()# XXX filter by access
        if len(boards) == 1:
            return redirect('card-list', board_id=boards[0].id)
        return redirect('board-list')
    return {}

@with_template('hello/login-form.html')
def delete_association(request):
    return {}