# Create your views here.

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.conf import settings
from kanbo.board.models import Board
from kanbo.shortcuts import with_template, returns_json

@with_template('about/home.html')
def home(request):
    board = Board.objects.get(id=1)
    return {'board': board}


@with_template('about/check-env.html')
def check_env(request):
    var_names = ['SITE_ORIGIN', 'SITE_NAME']
    return {
        'vars': [(var_name, getattr(settings, var_name)) for var_name in var_names],
    }