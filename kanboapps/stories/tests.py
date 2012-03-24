"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from kanboapps.stories.models import *


class TestNothing(TestCase):
    def test_nothing(self):
        pass

    def test_get_tag(self):
        bag = Bag(name='state', label='State')
        bag.save()
        new_tag = bag.tag_set.create(name='new')
        progress_tag = bag.tag_set.create(name='in-progress')
        done_tag = bag.tag_set.create(name='done')

        board = Board(label='a')
        board.save()
        story = board.story_set.create(label='This')
        story.tag_set.add(new_tag)

        self.assertEqual('new', story.get_tag(bag).name)

class TestTopsort(TestCase):
        class Thing(object):
                def __init__(self, id, succ_id):
                        self.id = id
                        self.succ_id = succ_id

                def __str__(self):
                        return '<thing{0}>'.format(self.id)

                def __repr__(self):
                        return 'Thing({0!r}, {1!r})'.format(self.id, self.succ_id)

        def test_nothing(self):
                things = []
                toposort(things)

                self.assertEqual([], things)

        def test_trivial(self):
                things = [TestTopsort.Thing(*w) for w in [(1, 2), (2, None), (3, 1)]]
                xs = list(things)
                toposort(xs)

                self.assertEqual([things[2], things[0], things[1]], xs)

        def test_stable_when_no_succs(self):
                things = [TestTopsort.Thing(*w) for w in [(1, 0), (2, None), (3, 0)]]
                xs = list(things)
                toposort(xs)

                self.assertEqual(things, xs)
