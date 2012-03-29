# -*- coding: UTF-8 -*-

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

    def test_break_cycles_if_necessary(self):
        things = [TestTopsort.Thing(*w) for w in [
            (1, 4), (2, 3), (3, 5), (4, 1), (5, 4),
        ]]
        xs = list(things)
        toposort(xs)

        self.assertEqual(5, len(xs))
        self.assertEqual(set(things), set(xs))

    def test_break_cycle_of_totality(self):
        things = [TestTopsort.Thing(*w) for w in [
           (1, 2), (2, 3), (3, 4), (4, 1),
        ]]
        xs = list(things)
        toposort(xs)

        self.assertEqual(4, len(xs))
        self.assertEqual(set(things), set(xs))

    def test_break_cycle_of_singleton(self):
        things = [TestTopsort.Thing(*w) for w in [
           (1, 2), (2, 3), (3, 3), (4, None),
        ]]
        xs = list(things)
        toposort(xs)

        self.assertEqual(4, len(xs))
        self.assertEqual(set(things), set(xs))

class TestRorderFromOrderedStories(TestCase):
    def setUp(self):
        # Create 7 stories in order.
        self.board = Board(label='boo')
        self.board.save()
        self.stories = [self.board.story_set.create(board=self.board, label=x, slug=x.lower())
                for x in ['Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf']]
        for x, y in zip(self.stories, self.stories[1:]):
            x.succ = y
            x.save()
        self.stories_by_slug = dict((x.slug, x) for x in self.stories)
        self.id_by_slug = dict((x.slug, x.id) for x in self.stories)

    def rearrange_and_check(self, order_slugs, expected_slugs):
        order = [(self.id_by_slug[x] if x else None) for x in order_slugs]
        rearrange_objects(Story, order)

        try:
            self.new_order = toposorted(Story.objects.all())
            failed = False
        except CyclesException:
            for obj in Story.objects.all():
                print obj.slug, obj.succ.slug if obj.succ else '--'
            failed = True
        self.assertFalse(failed, 'Could not toposort the result')
        self.slugs = [x.slug for x in self.new_order]
        self.assertEqual(expected_slugs, self.slugs)

    def test_nop_zero(self):
        # New orders are passed back as a list of IDs
        self.rearrange_and_check([],  ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf'])

    def test_nop_one(self):
        # Special conventon for adding sequence at end.
        self.rearrange_and_check(['alpha'],
            [ 'alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf',])

    def test_exchange_two(self):
        # This is supposed to be how drag & drop will work.
        self.rearrange_and_check(['foxtrot', 'echo'],
            ['alpha', 'bravo', 'charlie', 'delta', 'foxtrot', 'echo', 'golf'])

    def test_first_to_last(self):
        self.rearrange_and_check(['golf', 'alpha', 'bravo'],
            ['golf', 'alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot'])

    def test_gasther_and_plonk(self):
        self.rearrange_and_check(['bravo', 'echo', 'alpha', 'delta'],
            ['charlie', 'bravo', 'echo', 'alpha', 'delta', 'foxtrot', 'golf'])

    def test_dragon_drop_first_after_last(self):
        # Special conventon for adding sequence at end.
        self.rearrange_and_check(['alpha', None],
            ['bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'alpha',])

    def test_does_not_faile_when_cycles(self):
        # Again, cycles should never happen, but
        # if they do we need the system to self-correct.
        self.stories[-1].succ = self.stories[3]
        self.stories[-1].save()

        self.rearrange_and_check(['echo', 'golf'],
            [ 'alpha', 'bravo', 'charlie', 'delta', 'foxtrot', 'echo', 'golf'])

    def test_copes_with_singleton_cycle(self):
        # Again, cycles should never happen, but
        # if they do we need the system to self-correct.
        self.stories[3].succ = self.stories[3]
        self.stories[3].save()

        self.rearrange_and_check(['golf', 'delta', 'charlie', ],
            [ 'alpha', 'bravo', 'echo', 'foxtrot', 'golf', 'delta', 'charlie'])

    # The following are various permutations
    # that check the edge cases I can think of off the top
    # of my head. (No new code should be required.)

    def test_rearrange_everything(self):
        nu = ['delta', 'echo', 'charlie', 'alpha', 'foxtrot', 'bravo', 'golf']
        self.rearrange_and_check(nu, nu)

    def test_dragon_drop_last_before_first(self):
        self.rearrange_and_check(['golf', 'alpha'],
            [ 'golf', 'alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot',])

    def test_dragon_drop_middle_before_first(self):
        self.rearrange_and_check(['charlie', 'alpha'],
            [ 'charlie', 'alpha', 'bravo', 'delta', 'echo', 'foxtrot', 'golf'])

    def test_dragon_drop_second_before_first(self):
        self.rearrange_and_check(['bravo', 'alpha'],
            [ 'bravo', 'alpha', 'charlie', 'delta', 'echo', 'foxtrot', 'golf'])

    def test_dragon_drop_first_before_second(self):
        # Should be a no-op.
        self.rearrange_and_check(['alpha', 'bravo'],
            [ 'alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf'])

    def test_dragon_drop_first_before_middle(self):
        self.rearrange_and_check(['alpha', 'charlie'],
            ['bravo', 'alpha',  'charlie', 'delta', 'echo', 'foxtrot', 'golf'])

    def test_dragon_drop_first_before_last(self):
        self.rearrange_and_check(['alpha', 'golf'],
            ['bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'alpha',  'golf'])

    def test_dragon_drop_last_after_last(self):
        # Pointless, but what the hey.
        self.rearrange_and_check(['golf', ''],
            [ 'alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf'])

    def test_dragon_drop_penultimate_after_last(self):
        self.rearrange_and_check(['foxtrot', ''],
            [ 'alpha', 'bravo', 'charlie', 'delta', 'echo', 'golf', 'foxtrot'])

    def test_reverso(self):
        # Added because I discovered that reversing the
        # whole shebang caused a cycle to be created.
        nu = ['golf', 'foxtrot', 'echo', 'delta', 'charlie', 'bravo', 'alpha']
        self.rearrange_and_check(nu, nu)


class TestGridulate(TestCase):
    def setUp(self):
        # Create 16 stories
        self.board = Board.objects.create(label='z')
        self.stories = [self.board.story_set.create(board=self.board, label=x, slug=x)
                for x in 'abcdefghijklmnop']
        for x, y in zip(self.stories, self.stories[1:]):
            x.succ = y
            x.save()
        self.stories_by_slug = dict((x.slug, x) for x in self.stories)
        self.id_by_slug = dict((x.slug, x.id) for x in self.stories)

        # Create some bags
        self.bags = [self.board.bag_set.create(name=x) for x in 'qtw']
        self.tagss = [[b.tag_set.create(name=s) for s in ss]
            for b, ss in zip(self.bags, ['rs', 'uv', 'xyz'])]

        # Taggity tag
        for i, s in enumerate(self.stories):
            s.tag_set.add(self.tagss[0][i // 8])
            s.tag_set.add(self.tagss[1][i % 2])
            if i % 4:
                s.tag_set.add(self.tagss[2][i % 4 - 1])
            s.save()

    def test_fixture(self):
        self.assertEqual(['r', 'u'], [t.name for t in self.stories[0].tag_set.all()])
        self.assertEqual(['r', 'v', 'x'], [t.name for t in self.stories[1].tag_set.all()])

    def test_simplest(self):
        subject = self.board.make_grid()

        # One row containing onc cell containing all the stories.
        self.assertEqual(Grid([
            GridRow([
                GridCol(self.stories)
            ])
        ]), subject)

    def test_columns(self):
        subject = self.board.make_grid(self.bags[0])

        # One row containing 3 cells, the first empty
        self.assertEqual(Grid([
            GridRow([
                GridCol(self.stories[:8], [self.tagss[0][0]]),
                GridCol(self.stories[8:], [self.tagss[0][1]]),
            ])
        ]), subject)


    def test_column_zero_has_unmatched_stories(self):
        subject = self.board.make_grid(self.bags[2])

        # One row containing 4 cells, each with one quarter of the items.
        self.assertEqual(Grid([
            GridRow([
                GridCol([self.stories[i] for i in [0, 4, 8, 12]]),
                GridCol([self.stories[i] for i in [1, 5, 9, 13]], [self.tagss[2][0]]),
                GridCol([self.stories[i] for i in [2, 6, 10, 14]], [self.tagss[2][1]]),
                GridCol([self.stories[i] for i in [3, 7, 11, 15]], [self.tagss[2][2]]),
            ])
        ]), subject)