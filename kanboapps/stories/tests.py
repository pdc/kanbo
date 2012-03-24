"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
#from kanboapps.stories.models import *


class TestNothing(TestCase):
    def test_nothing(self):
        pass
        
    #def test_get_tags(self):
    #    bag = Bag(name='state', label='State')
    #    bag.save()
    #    new_tag = Bag.tag_set.create(name='new')
    #    progress_tag = Bag.tag_set.create(name='progress')
    #    done_tag = Bag.tag_set.create(name='done')
    #    
    #    board = Board(label='a')
    #    board.save()
    #    story = Board.story_set.create(label='This')
    #    story.tag_set.add(new_tag)
    #    
    #    self.assertEqual('new', story.get_tags(bag).name)