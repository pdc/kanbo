# Create your views here.

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from kanboapps.board.models import Board
from kanboapps.shortcuts import with_template, returns_json

@with_template('about/home.html')
def home(request):
    board = Board.objects.get(id=1)
    return {'board': board}