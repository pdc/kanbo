# -*- coding: UTF-8 -*-

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, Client
from mock import patch
import redis
import fakeredis
import json
from django.contrib.auth.models import User, AnonymousUser
from kanboapps.board.models import *
from kanboapps.board.views import BoardForm
from kanboapps.board import models

class TestCard(TestCase):
    def test_nothing(self):
        pass

    def test_get_tag(self):
        bag = Bag(name='state')
        bag.save()
        new_tag = bag.tag_set.create(name='new')
        progress_tag = bag.tag_set.create(name='in-progress')
        done_tag = bag.tag_set.create(name='done')

        owner = User.objects.create(username='pop')
        board = owner.board_set.create(label='a')
        card = board.card_set.create(label='This')
        card.tag_set.add(new_tag)

        self.assertEqual('new', card.get_tag(bag).name)


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


class TestRearrangeOrderedStories(TestCase):
    def setUp(self):
        # Create 7 cards in order.
        self.owner = User.objects.create(username='xerxes')
        self.board = self.owner.board_set.create(label='boo')
        self.cards = [self.board.card_set.create(board=self.board, label=x, name=x.lower())
                for x in ['Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf']]
        for x, y in zip(self.cards, self.cards[1:]):
            x.succ = y
            x.save()
        self.cards_name = dict((x.name, x) for x in self.cards)
        self.id_name = dict((x.name, x.id) for x in self.cards)

    def rearrange_and_check(self, order_names, expected_names):
        order = [(self.id_name[x] if x else None) for x in order_names]
        rearrange_objects(Card.objects, order)

        try:
            self.new_order = toposorted(Card.objects.all())
            failed = False
        except CyclesException:
            for obj in Card.objects.all():
                print obj.name, obj.succ.name if obj.succ else '--'
            failed = True
        self.assertFalse(failed, 'Could not toposort the result')
        self.names = [x.name for x in self.new_order]
        self.assertEqual(expected_names, self.names)

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
        self.cards[-1].succ = self.cards[3]
        self.cards[-1].save()

        self.rearrange_and_check(['echo', 'golf'],
            [ 'alpha', 'bravo', 'charlie', 'delta', 'foxtrot', 'echo', 'golf'])

    def test_copes_with_singleton_cycle(self):
        # Again, cycles should never happen, but
        # if they do we need the system to self-correct.
        self.cards[3].succ = self.cards[3]
        self.cards[3].save()

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


class BoardFixtureMixin(object):
    def create_board_and_accoutrements(self):
        # Create 16 cards
        self.owner = User.objects.create(username='derpyhooves')
        self.owner.set_password('jubilee')
        self.owner.save()

        self.board = self.owner.board_set.create(name='z', label='Z')
        self.cards = [self.board.card_set.create(board=self.board, label=x, name=x)
                for x in 'abcdefghijklmnop']
        for x, y in zip(self.cards, self.cards[1:]):
            x.succ = y
            x.save()
        self.cards_name = dict((x.name, x) for x in self.cards)
        self.id_name = dict((x.name, x.id) for x in self.cards)

        # Create some bags
        self.bags = [self.board.bag_set.create(name=x) for x in 'qtw']
        self.tagss = [[b.tag_set.create(name=s) for s in ss]
            for b, ss in zip(self.bags, ['rs', 'uv', 'xyz'])]

        # Taggity tag
        for i, s in enumerate(self.cards):
            s.tag_set.add(self.tagss[0][i // 8])
            s.tag_set.add(self.tagss[1][i % 2])
            if i % 4:
                s.tag_set.add(self.tagss[2][i % 4 - 1])
            s.save()

    def reload_cards(self):
        self.cards = [Card.objects.get(id=s.id) for s in self.cards]

    def assert_grids_equal(self, grid1, grid2):
        self.assertTrue(grid1)
        self.assertTrue(grid2)
        self.assertEqual(len(grid1.rows), len(grid2.rows))
        for row1, row2 in zip(grid1.rows, grid2.rows):
            self.assertEqual(row1.tags, row2.tags)
            self.assert_grid_rows_equal(row1, row2)

    def assert_grid_rows_equal(self, row1, row2):
        self.assertEqual(len(row1.bins), len(row2.bins))
        for bin1, bin2 in zip(row1.bins, row2.bins):
            self.assertEqual(bin1.tags, bin2.tags)
            self.assertEqual(bin1.cards, bin2.cards)


class TestUrls(TestCase, BoardFixtureMixin):
    def setUp(self):
        self.create_board_and_accoutrements()

    def test_board_has_absolute_url(self):
        self.assertEqual('/derpyhooves/z/grids/q', self.board.get_absolute_url())

    def test_bag_has_new_tag_url(self):
        self.assertEqual('/derpyhooves/z/bags/q/tags/new', self.bags[0].get_new_tag_url())


class TestGrid(TestCase, BoardFixtureMixin):
    def setUp(self):
        self.create_board_and_accoutrements()

    def test_fixture(self):
        self.assertEqual(['r', 'u'], [t.name for t in self.cards[0].tag_set.all()])
        self.assertEqual(['r', 'v', 'x'], [t.name for t in self.cards[1].tag_set.all()])

    def test_simplest(self):
        subject = self.board.make_grid()

        # One row containing onc cell containing all the cards.
        self.assert_grids_equal(Grid([
            GridRow([
                GridBin(self.cards)
            ])
        ]), subject)

    def test_columns(self):
        subject = self.board.make_grid(self.bags[0])

        # One row containing 3 cells, the first empty
        self.assert_grids_equal(Grid([
            GridRow([
                GridBin([]),
                GridBin(self.cards[:8], [self.tagss[0][0]]),
                GridBin(self.cards[8:], [self.tagss[0][1]]),
            ])
        ]), subject)

    def test_column_zero_has_unmatched_cards(self):
        subject = self.board.make_grid(self.bags[2])

        # One row containing 4 cells, each with one quarter of the items.
        self.assert_grids_equal(Grid([
            GridRow([
                GridBin([self.cards[i] for i in [0, 4, 8, 12]]),
                GridBin([self.cards[i] for i in [1, 5, 9, 13]], [self.tagss[2][0]]),
                GridBin([self.cards[i] for i in [2, 6, 10, 14]], [self.tagss[2][1]]),
                GridBin([self.cards[i] for i in [3, 7, 11, 15]], [self.tagss[2][2]]),
            ])
        ]), subject)


class TestCardReplacingTags(TestCase, BoardFixtureMixin):
    def setUp(self):
        self.create_board_and_accoutrements()

    def test_replace_one_existing_tag(self):
        self.cards[0].replace_tags(
            axes=[self.bags[0]],
            tags=[self.tagss[0][1]])
        self.reload_cards()

        self.assertEqual(self.tagss[0][1],
            self.cards[0].get_tag(self.bags[0]))

    def test_replace_one_existing_tag_with_nothing(self):
        self.cards[0].replace_tags(
            axes=[self.bags[0]],
            tags=[])
        self.reload_cards()

        with self.assertRaises(Tag.DoesNotExist):
            self.cards[0].get_tag(self.bags[0])

    def test_replace_one_existing_tag_id(self):
        self.cards[0].replace_tags(
            axes=[self.bags[0].id],
            tags=[self.tagss[0][1].id])
        self.reload_cards()

        self.assertEqual(self.tagss[0][1],
            self.cards[0].get_tag(self.bags[0]))


class FakeRedisMixin(object):
    #@patch.object(models, 'get_redis')
    def prepare_event_repeater(self):
        #stubbed_get_redis.return_value = fakeredis.FakeRedis()
        self.event_repeater = EventRepeater()
        self.assertTrue(isinstance(self.event_repeater.redis, fakeredis.FakeRedis))
        self.event_repeater.redis.flushall()


class TestEventRepeater(TestCase, FakeRedisMixin):
    def setUp(self):
        self.prepare_event_repeater()

    def test_no_events(self):
        strm = self.event_repeater.get_stream(57)
        self.assertEqual(0, strm.next_seq())
        self.assertEqual(('[]', 0), strm.as_json_starting_from(0))

    def test_one_event(self):
        strm = self.event_repeater.get_stream(13)
        event = dict(marshmellow='banana', frog=['toad', 'ratty'])
        res = strm.append(event)

        strm2 = self.event_repeater.get_stream(13)
        self.assertEqual(1, strm2.next_seq())
        self.assertEqual([event], json.loads(strm2.as_json_starting_from(0)[0]))
        self.assertEqual(1, strm2.as_json_starting_from(0)[1])
        self.assertEqual(('[]', 1), strm2.as_json_starting_from(1))

    def test_several_events(self):
        strm = self.event_repeater.get_stream(99)
        events = [{'foo': x} for x in ['bar', 'baz', 'quux']]
        for event in events:
            res = strm.append(event)

        strm2 = self.event_repeater.get_stream(99)
        for i in range(len(events) + 1):
            self.assertEqual((json.dumps(events[i:]), 3), strm2.as_json_starting_from(i))

    def test_several_events_interrupted(self):
        strm = self.event_repeater.get_stream(42)
        events = [{'foo': x} for x in ['bar', 'baz', 'quux', 'quux2']]
        for event in events[:2]:
            res = strm.append(event)

        # Simulate expiry of the list key:
        strm.redis.delete(strm.k_list)

        # Now continue with the events.
        for event in events[2:]:
            res = strm.append(event)

        # Events after the expiry are available.
        strm2 = self.event_repeater.get_stream(42)
        for i in range(3, len(events)):
            self.assertEqual((json.dumps(events[i:]), 4), strm2.as_json_starting_from(i))

    def test_raises_when_request_is_too_late(self):
        strm = self.event_repeater.get_stream(42)
        events = [{'foo': x} for x in ['bar', 'baz', 'quux', 'quux2']]
        for event in events:
            res = strm.append(event)

        # Simulate expiry of the list key:
        strm.redis.delete(strm.k_list)

        # Attempts to get info from before start leads to misery.
        strm2 = self.event_repeater.get_stream(42)
        with self.assertRaises(EventsExpired):
            strm2.as_json_starting_from(2)


class TestEventsAreSaved(TestCase, BoardFixtureMixin, FakeRedisMixin):
    def setUp(self):
        self.prepare_event_repeater()
        self.create_board_and_accoutrements()
        self.client = Client()


    def test_rearrangement_creates_events(self):
        self.client.login(username='derpyhooves', password='jubilee')

        params = {
            'order': '2 1',
            'dropped': '2',
             'tags': str(self.tagss[0][1].id),
         }
        self.client.post('/boards/1/grids/q/rearrangement', params)
        jevs, next_seq = self.event_repeater.get_stream(1).as_json_starting_from(0)

        self.assertEqual(1, next_seq)

        expected = {
            'type': 'rearrange',
            'board': 1,
            'xaxis':  [self.bags[0].id],
            'order': [2, 1],
            'dropped': 2,
            'tags': [self.tagss[0][1].id],
        }
        self.assertEqual([expected], json.loads(jevs))

    def test_when_not_owner_rearrangement_is_forbidden(self):
        other = User.objects.create(username='eve')
        other.set_password('7wi1i8h7')
        other.save()

        self.client.login(username='eve', password='7wi1i8h7')

        params = {
            'order': '2 1',
            'dropped': '2',
             'tags': str(self.tagss[0][1].id),
         }
        response = self.client.post('/boards/1/grids/q/rearrangement', params)

        self.assertEqual(403, response.status_code)


class TestBoardMembership(TestCase):
    def setUp(self):
        self.alice = User.objects.create(username='Alice')
        self.bob = User.objects.create(username='Bob')
        self.charley = User.objects.create(username='Charley')
        self.dick = User.objects.create(username='Dick')

        self.subject = self.alice.board_set.create(name='derp')

        Access.objects.create(user=self.bob, board=self.subject)
        Access.objects.create(user=self.dick, board=self.subject, can_rearrange=False)

    def test_fixture(self):
        pass

    def test_alice_can_rearrange_board(self):
        self.assertTrue(self.subject.allows_rearrange(self.alice))

    def test_bob_can_rearrange_board(self):
        self.assertTrue(self.subject.allows_rearrange(self.bob))

    def test_charley_cannot_rearrange_board(self):
        self.assertFalse(self.subject.allows_rearrange(self.charley))

    def test_dick_cannot_rearrange_board(self):
        self.assertFalse(self.subject.allows_rearrange(self.dick))

    def test_anonymous_cannot_rearrange_board(self):
        anon = AnonymousUser()
        self.assertFalse(self.subject.allows_rearrange(anon))


class TestPublicBoardMembership(TestCase):
    def setUp(self):
        self.alice = User.objects.create(username='Alice')
        self.bob = User.objects.create(username='Bob')

        self.subject = self.bob.board_set.create(name='yup', is_public=True)

    def test_is_rearrangeable_by_owner(self):
        self.assertTrue(self.subject.allows_rearrange(self.bob))

    def test_is_rearrangeable_by_others(self):
        self.assertTrue(self.subject.allows_rearrange(self.alice))

    def test_is_rearrangeable_by_anon(self):
        self.assertTrue(self.subject.allows_rearrange(AnonymousUser()))




