# -*- coding: UTF-8 -*-

"""
Run te tests with

    ./manage.py test board
"""

from django.test import TestCase, Client
from mock import patch

import redis
import fakeredis
import json
from pprint import pprint
from django.contrib.auth.models import User, AnonymousUser
from kanbo.utils import url_fix
from kanbo.board.models import *
from kanbo.board.forms import BoardForm, BagForm, TagForm
from kanbo.board import models

class TestCard(TestCase):
    def test_nothing(self):
        pass

    def test_get_tag(self):
        self.given_a_board()
        self.given_a_card_with_tag()

        self.assertEqual('new', self.card.get_tag(self.bag).name)

    def test_when_has_href(self):
        self.given_a_board()
        self.given_a_card_with_href()

        self.when_asked_for_view_href()

        self.then_click_href_should_equal_href_attribute()

    def test_when_hasnt_href(self):
        self.given_a_board()
        self.given_a_card_without_href()

        self.when_asked_for_view_href()

        self.then_click_href_should_equal_nothing()

    def test_owner_can_get_edit_path(self):
        self.given_a_board()
        self.given_a_card_with_href()

        self.when_asked_for_edit_href()

        self.then_click_href_should_equal_edit_url()

    def test_non_owner_gets_nothing(self):
        self.given_a_board()
        self.given_a_card_with_href()
        self.given_another_user()

        self.when_other_user_asks_for_edit_href()

        self.then_click_href_should_equal_nothing()

    def test_click_href_included_in_grid(self):
        self.given_a_board()
        self.given_a_card_with_href()

        self.when_rendering_the_grid_for(self.owner, 'view')

        self.then_should_be_success()
        self.and_click_options_should_include_edit()
        self.and_should_have_grid_with_card_with_click_href()
        self.then_click_href_should_equal_href_attribute()

    def test_when_owner_edit_href_included_in_grid(self):
        self.given_a_board()
        self.given_a_card_with_href()

        self.when_rendering_the_grid_for(self.owner, 'edit')

        self.then_should_be_success()
        self.and_click_options_should_include_edit()
        self.and_should_have_grid_with_card_with_click_href()
        self.then_click_href_should_equal_edit_url()

    def test_when_not_owner_edit_href_not_included_in_grid(self):
        self.given_a_board()
        self.given_a_card_with_href()
        self.given_another_user()

        self.when_rendering_the_grid_for(self.user2, 'view')

        self.then_should_be_success()
        self.and_click_options_should_not_include_edit()

    def test_when_edit_permission_edit_href_is_include_after_all(self):
        self.given_a_board()
        self.given_a_card_with_href()
        self.given_another_user()
        self.given_other_user_has_edit_privileges()

        self.when_rendering_the_grid_for(self.owner, 'view')

        self.then_should_be_success()
        self.and_click_options_should_include_edit()

    # Helpers for the above tests

    def given_a_board(self):
        self.owner = User.objects.create(username='pop')
        self.owner.set_password('x')
        self.owner.save()
        self.board = self.owner.board_set.create(name='a')

        self.bag = self.board.bag_set.create(name='state')
        self.new_tag = self.bag.tag_set.create(name='new')
        self.progress_tag = self.bag.tag_set.create(name='in-progress')
        self.done_tag = self.bag.tag_set.create(name='done')

    def given_a_card_with_tag(self):
        self.card = self.board.card_set.create(label='This')
        self.card.tag_set.add(self.new_tag)

    def given_a_card_with_href(self):
        self.card = self.board.card_set.create(name='card2', label='Card 2',
                href='HREF_ATTRIBUTE_VALUE')

    def given_a_card_without_href(self):
        self.card = self.board.card_set.create(name='card3', label='Card 3')

    def given_another_user(self):
        self.user2 = User.objects.create(username='bang')
        self.user2.set_password('x')
        self.user2.save()

    def given_other_user_has_edit_privileges(self):
        Access.objects.create(user=self.user2, board=self.board, can_rearrange=True)

    def when_asked_for_href(self, user, which):
        self.result = self.card.get_click_href(user, AxisSpec([self.bag], [], click=which))

    def when_asked_for_view_href(self):
        self.when_asked_for_href(self.owner, 'view')

    def when_asked_for_edit_href(self):
        self.when_asked_for_href(self.owner, 'edit')

    def when_other_user_asks_for_edit_href(self):
        self.when_asked_for_href(self.user2, 'edit')

    def when_rendering_the_grid_for(self, user, which):
        self.client = Client()
        self.client.login(username=user.username, password='x')

        u = '/pop/a/grids/state'
        if which != 'view':
            u += ';click=' + which
        u += '/'
        self.response = self.client.get(u)

    def then_click_href_should_equal_href_attribute(self):
        self.assertEqual('HREF_ATTRIBUTE_VALUE', self.result)

    def then_click_href_should_equal_edit_url(self):
        self.assertEqual(url_fix('/pop/a/grids/state;click=edit/card2/edit'), url_fix(self.result))

    def then_click_href_should_equal_nothing(self):
        self.assertFalse(self.result)

    def then_should_be_success(self):
        self.assertEqual(200, self.response.status_code)

    def and_should_have_grid_with_card_with_click_href(self):
        self.grid = self.response.context['grid']
        for card in [card for row in self.grid.rows
                for bin in row.bins
                    for card in bin.cards]:
            self.grid_card = card
            break
        else:
            self.fail('expected to find card in grid in context of response')
        self.assertTrue(hasattr(self.grid_card, 'click_href'), 'expected click_href attribute to be added')
        self.result = self.grid_card.click_href

    def and_click_options_should_include_edit(self):
        self.assertEqual(['view', 'edit'], [x.name for x in self.response.context['click_options']])

    def and_click_options_should_not_include_edit(self):
        self.assertEqual(['view'], [x.name for x in self.response.context['click_options']])



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

        # Create three bags
        self.bags = [self.board.bag_set.create(name=x) for x in 'qtw']
        self.tagss = [[b.tag_set.create(name=s) for s in ss]
            for b, ss in zip(self.bags, ['rs', 'uv', 'xyz'])]

        # Tag then
        for i, card in enumerate(self.cards):
            card.tag_set.add(self.tagss[0][i // 8]) # First half q:r, second half q:3
            card.tag_set.add(self.tagss[1][i % 2]) # Alternate t:u and t:v
            if i % 4:
                card.tag_set.add(self.tagss[2][i % 4 - 1]) # Cycle through (blank), w:x, w:y, w:z
            card.save()

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
        self.assertEqual('/derpyhooves/z/grids/q/', self.board.get_absolute_url())

    def test_bag_has_new_tag_url(self):
        self.assertEqual('/derpyhooves/z/bags/q/tags/new', self.bags[0].get_new_tag_url())


class TestGrid(TestCase, BoardFixtureMixin):
    def setUp(self):
        self.create_board_and_accoutrements()

    def test_fixture(self):
        self.assertEqual(['r', 'u'], [t.name for t in self.cards[0].tag_set.all()])
        self.assertEqual(['r', 'v', 'x'], [t.name for t in self.cards[1].tag_set.all()])

    def test_simplest(self):
        subject = self.board.make_grid(AxisSpec(None, None))

        # One row containing onc cell containing all the cards.
        self.assert_grids_equal(Grid([
            GridRow([
                GridBin(self.cards)
            ])
        ]), subject)

    def test_columns(self):
        subject = self.board.make_grid(AxisSpec([self.bags[0]], None))

        # One row containing 3 cells, the first empty
        self.assert_grids_equal(Grid([
            GridRow([
                GridBin([]),
                GridBin(self.cards[:8], [self.tagss[0][0]]),
                GridBin(self.cards[8:], [self.tagss[0][1]]),
            ])
        ]), subject)

    def test_column_zero_has_unmatched_cards(self):
        subject = self.board.make_grid(AxisSpec([self.bags[2]], None))

        # One row containing 4 cells, each with one quarter of the items.
        self.assert_grids_equal(Grid([
            GridRow([
                GridBin([self.cards[i] for i in [0, 4, 8, 12]]),
                GridBin([self.cards[i] for i in [1, 5, 9, 13]], [self.tagss[2][0]]),
                GridBin([self.cards[i] for i in [2, 6, 10, 14]], [self.tagss[2][1]]),
                GridBin([self.cards[i] for i in [3, 7, 11, 15]], [self.tagss[2][2]]),
            ])
        ]), subject)

    def test_when_y_axis_specified_should_generate_2_rows(self):
        subject = self.board.make_grid(AxisSpec([self.bags[0]], [self.bags[1]]))

        # _   q:r  q:s
        # t:u 0246 8ACE # evens
        # t:v 1357 9BDF # Odds

        # Three rows of three cells, with the first row and column calls all empty.

        self.assert_grids_equal(Grid([
            GridRow([
                GridBin([], []),
                GridBin([], [self.tagss[0][0]]),
                GridBin([], [self.tagss[0][1]])]),
            GridRow([
                GridBin([], [self.tagss[1][0]]),
                GridBin([self.cards[i] for i in [0, 2, 4, 6]], [self.tagss[0][0], self.tagss[1][0]]),
                GridBin([self.cards[i] for i in [8, 10, 12, 14]], [self.tagss[0][1], self.tagss[1][0]])]),
            GridRow([
                GridBin([], [self.tagss[1][1]]),
                GridBin([self.cards[i] for i in [1, 3, 5, 7]], [self.tagss[0][0], self.tagss[1][1]]),
                GridBin([self.cards[i] for i in [9, 11, 13, 15]], [self.tagss[0][1], self.tagss[1][1]])])]), subject)


class TagParsingBehaviour(TestCase, BoardFixtureMixin):
    def setUp(self):
        # Create intentionally repetative names to try to catch myself out!
        self.user = User.objects.create(username='mr-user')
        self.board1 = self.user.board_set.create(name='board1name')
        self.board2 = self.user.board_set.create(name='board2name')
        self.bag1a = self.board1.bag_set.create(name='baga')
        self.bag1b = self.board1.bag_set.create(name='bagb')
        self.bag2a = self.board2.bag_set.create(name='baga')
        self.bag2b = self.board2.bag_set.create(name='bagb')
        self.tag1ai = self.bag1a.tag_set.create(name='tagi')
        self.tag1aii = self.bag1a.tag_set.create(name='tagii')
        self.tag1aiii = self.bag1a.tag_set.create(name='tagiii')
        self.tag1bi = self.bag1b.tag_set.create(name='tagi')
        self.tag1bii = self.bag1b.tag_set.create(name='tagii')
        self.tag1biii = self.bag1b.tag_set.create(name='tagiii')
        self.tag2ai = self.bag2a.tag_set.create(name='tagi')
        self.tag2aii = self.bag2a.tag_set.create(name='tagii')
        self.tag2aiii = self.bag2a.tag_set.create(name='tagiii')
        self.tag2bi = self.bag2b.tag_set.create(name='tagi')
        self.tag2bii = self.bag2b.tag_set.create(name='tagii')
        self.tag2biii = self.bag2b.tag_set.create(name='tagiii')

    def test_given_a_tag_should_return_it(self):
        self.assertEqual(self.tag1ai, self.board1.parse_tag(self.tag1ai))
        self.assertEqual(self.tag2bii, self.board2.parse_tag(self.tag2bii))

    def test_given_an_int_should_return_tag_with_that_id(self):
        self.assertEqual(self.tag2aii, self.board2.parse_tag(self.tag2aii.id))
        self.assertEqual(self.tag1biii, self.board1.parse_tag(self.tag1biii.id))

    def test_given_string_should_return_named_tag(self):
        self.assertEqual(self.tag1biii, self.board1.parse_tag('bagb:tagiii'))
        self.assertEqual(self.tag2ai, self.board2.parse_tag('baga:tagi'))

    def test_given_a_stringified_int_should_return_tag_with_that_id(self):
        self.assertEqual(self.tag2bi, self.board2.parse_tag(str(self.tag2bi.id)))
        self.assertEqual(self.tag1aii, self.board1.parse_tag(str(self.tag1aii.id)))

    def test_given_a_stringified_int_for_wrong_board_it_should_fail(self):
        with self.assertRaises(Tag.DoesNotExist):
            self.board1.parse_tag(str(self.tag2bi.id))


class TestCardReplacingTags(TestCase, BoardFixtureMixin):
    def setUp(self):
        self.create_board_and_accoutrements()

    def test_replace_one_existing_tag(self):
        self.cards[0].replace_tags(
            axis_spec=AxisSpec([self.bags[0]], None),
            tags=[self.tagss[0][1]])
        self.reload_cards()

        self.assertEqual(self.tagss[0][1],
            self.cards[0].get_tag(self.bags[0]))

    def test_replace_one_existing_tag_with_nothing(self):
        self.cards[0].replace_tags(
            axis_spec=AxisSpec([self.bags[0]], None),
            tags=[])
        self.reload_cards()

        with self.assertRaises(Tag.DoesNotExist):
            self.cards[0].get_tag(self.bags[0])

    def test_replace_one_existing_tag_id(self):
        self.cards[0].replace_tags(
            axis_spec=AxisSpec([self.bags[0]], None),
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

    def test_card_arrangement_creates_events(self):
        self.client.login(username='derpyhooves', password='jubilee')

        params = {
            'order': '2 1',
            'dropped': '2',
             'tags': str(self.tagss[0][1].id),
         }
        self.client.post('/boards/1/grids/q/arrangement', params)
        jevs, next_seq = self.event_repeater.get_stream(1).as_json_starting_from(0)

        self.assertEqual(1, next_seq)

        expected = {
            u'type': 'rearrange',
            u'board': 1,
            u'xaxis':  [self.bags[0].id],
            u'yaxis':  [],
            u'order': [2, 1],
            u'dropped': 2,
            u'tags': [self.tagss[0][1].id],
        }
        self.assertEqual([expected], json.loads(jevs))

    def test_when_not_owner_card_arrangement_is_forbidden(self):
        other = User.objects.create(username='eve')
        other.set_password('7wi1i8h7')
        other.save()

        self.client.login(username='eve', password='7wi1i8h7')

        params = {
            'order': '2 1',
            'dropped': '2',
             'tags': str(self.tagss[0][1].id),
         }
        response = self.client.post('/boards/1/grids/q/arrangement', params)

        self.assertEqual(403, response.status_code)


class TestBoardMembership(TestCase):
    def setUp(self):
        self.alice = User.objects.create(username='Alice')
        self.bob = User.objects.create(username='Bob')
        self.charley = User.objects.create(username='Charley')
        self.dick = User.objects.create(username='Dick')

        self.subject = self.alice.board_set.create(name='derp')
        self.bag = self.subject.bag_set.create(name='bagname')

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

    def test_owner_has_two_click_options(self):
        click_options = self.subject.get_click_options(self.alice, AxisSpec([self.bag], []))
        self.assertEqual(2, len(click_options))
        self.assertEqual('view', click_options[0].name)
        self.assertEqual('/Alice/derp/grids/bagname/', click_options[0].href)
        self.assertEqual('edit', click_options[1].name)
        print url_fix(click_options[1].href)
        self.assertEqual(url_fix('/Alice/derp/grids/bagname;click=edit/'), url_fix(click_options[1].href))


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


class TestSortingTags(TestCase, BoardFixtureMixin):
    def setUp(self):
        self.bag = Bag.objects.create(name='bonk')
        self.tags = [self.bag.tag_set.create(name=x) for x in 'fred']
        self.tags_by_name = dict((x.name, x) for x in self.tags)
        self.ids_by_name = dict((x.name, x.id) for x in self.tags)

    def test_default_order_is_creation_order(self):
        self.assertEqual('f r e d'.split(), [x.name for x in self.bag.tags_sorted()])

    def test_rearrange(self):
        ids = [self.ids_by_name[x] for x in 'e r d'.split()]
        rearrange_objects(self.bag.tag_set, ids)
        self.assertEqual('f e r d'.split(), [x.name for x in self.bag.tags_sorted()])


class TestBagFormIncludesInialTags(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='username')
        self.board = self.user.board_set.create(name='boardname')

    def test_has_inital_tags_field(self):
        subject = BagForm({'name': 'foo', 'initial_tags': 'tag1\ntag2'}, instance=Bag(board=self.board))

        self.assertTrue(subject.is_valid())
        self.assertEqual('tag1\ntag2', subject.cleaned_data['initial_tags'])

    def test_requires_lowercase(self):
        subject = BagForm({'name': 'Foo', 'initial_tags': 'tag1\ntag2'}, instance=Bag(board=self.board))

        self.assertFalse(subject.is_valid())

    def test_forbids_spaces_in_tags(self):
        subject = BagForm({'name': 'foo', 'initial_tags': 'too many spaces\nanother spacy tag'}, instance=Bag(board=self.board))

        self.assertFalse(subject.is_valid())

    def test_when_initial_tags_has_three_items_it_should_be_valid(self):
        text = """head
toes
liver"""
        subject = BagForm({'name': 'foo', 'initial_tags': text}, instance=Bag(board=self.board))

        self.assertTrue(subject.is_valid())


class TestTagFormChecksUniqueness(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='username')
        self.board = self.user.board_set.create(name='boardname')
        self.bag = self.board.bag_set.create(name='bagname')
        self.tags = [self.bag.tag_set.create(name=x) for x in 'lmnop']

    def test_when_tag_exists_form_should_be_invalid(self):
        subject = TagForm({'name': 'p'}, instance=Tag(bag=self.bag))

        self.assertFalse(subject.is_valid())

    def test_when_tag_is_new_form_should_be_valid(self):
        subject = TagForm({'name': 'zz9'}, instance=Tag(bag=self.bag))

        self.assertTrue(subject.is_valid())

class DeleteBagBehaviour(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='username')
        self.user.set_password('userpassword')
        self.user.save()

        self.other = User.objects.create(username='othername')
        self.other.set_password('otherpassword')
        self.other.save()

        self.board = self.user.board_set.create(name='boardname')
        self.bag = self.board.bag_set.create(name='bagname')
        self.tags = [self.bag.tag_set.create(name=x) for x in 'lmnop']

        self.other_bag = self.board.bag_set.create(name='otherbag')
        self.other_tags = [self.other_bag.tag_set.create(name=x) for x in 'pqrst']

        # self.client = Client()

    def test_when_logged_in_as_owner_it_should_allow_link(self):
        self.client.login(username='username', password='userpassword')

        response = self.client.get('/username/boardname/bags/bagname/')

        self.assertTrue(response.context['allows_delete'])

    def test_when_logged_in_as_other_it_should_not_allow_link(self):
        self.client.login(username='othernane', password='otherpassword')

        response = self.client.get('/username/boardname/bags/bagname/')

        self.assertFalse(response.context['allows_delete'])

    def test_when_not_logged_in_it_should_redirect(self):
        response = self.client.get('/username/boardname/bags/bagname/delete')

        self.assertEqual(302, response.status_code)

    def test_when_logged_in_as_someone_else_it_should_redirect(self):
        self.client.login(username='othername', password='otherpassword')

        response = self.client.get('/username/boardname/bags/bagname/delete')

        self.assertRedirects(response, '/username/boardname/')

    def test_when_logged_in_as_owner_it_should_show_form(self):
        self.client.login(username='username', password='userpassword')

        response = self.client.get('/username/boardname/bags/bagname/delete')

        self.assertEqual(200, response.status_code)
        self.assertEqual(self.bag, response.context['bag'])

    def test_when_posting_as_owner_it_should_delete_bag(self):
        self.client.login(username='username', password='userpassword')

        response = self.client.post('/username/boardname/bags/bagname/delete')

        self.assertRedirects(response, '/username/boardname/')
        self.assertEqual(1, Bag.objects.filter(board=self.board).count()) # No longer in db
        self.assertEqual(0, Tag.objects.filter(bag=self.bag).count()) # Also delets dependents
        self.assertEqual(5, self.other_bag.tag_set.count()) # Doesn‘t delete anything else



class BoardStepsMixin(object):
    def given_a_board_with_one_bag(self):
        self.user = User.objects.create(username='username')
        self.user.set_password('userpassword')
        self.user.save()
        self.board = self.user.board_set.create(name='boardname')
        self.bag = self.board.bag_set.create(name='bagname')
        self.tags = [self.bag.tag_set.create(name=n) for n in ['ape', 'bee']]

    def given_a_board_with_two_bags(self):
        self.given_a_board_with_one_bag()
        self.bag2 =  self.board.bag_set.create(name='secondbag')
        self.tags2 = [self.bag2.tag_set.create(name=n) for n in ['cat', 'dog']]

    def given_a_board_with_three_bags(self):
        self.given_a_board_with_two_bags()
        self.bag3 =  self.board.bag_set.create(name='thirdbag')
        self.tags3 = [self.bag2.tag_set.create(name=n) for n in ['eel', 'fox']]

    def given_a_one_by_none_axis_spec(self):
        self.given_a_board_with_one_bag()
        self.axis_spec = AxisSpec([self.bag], None)

    def given_a_one_by_one_axis_spec(self):
        self.given_a_board_with_two_bags()
        self.axis_spec = AxisSpec([self.bag], [self.bag2])

    def given_logged_in_as_owner(self):
        self.client.login(username='username', password='userpassword')


class AxisSpecEquality(TestCase, BoardStepsMixin):
    def test_when_same_x_and_y_axes_should_return_true(self):
        self.given_a_board_with_two_bags()

        self.assertTrue(AxisSpec([self.bag], None) == AxisSpec([self.bag], None))
        self.assertTrue(AxisSpec([self.bag], [self.bag2]) == AxisSpec([self.bag], [self.bag2]))
        self.assertTrue(AxisSpec([self.bag, self.bag2], None) == AxisSpec([self.bag, self.bag2], None))

    def test_when_not_same_x_and_y_axes_should_return_false(self):
        self.given_a_board_with_two_bags()

        self.assertFalse(AxisSpec([self.bag], None) == AxisSpec([self.bag2], None))
        self.assertFalse(AxisSpec([self.bag], [self.bag2]) == AxisSpec([self.bag2], [self.bag]))
        self.assertFalse(AxisSpec([self.bag, self.bag2], None) == AxisSpec([self.bag2, self.bag], None))


class AxisSpecEquality(TestCase, BoardStepsMixin):
    def test_when_same_x_and_y_axes_should_return_true(self):
        self.given_a_board_with_two_bags()

        self.assertTrue(AxisSpec([self.bag], None) == AxisSpec([self.bag], None))
        self.assertTrue(AxisSpec([self.bag], [self.bag2]) == AxisSpec([self.bag], [self.bag2]))
        self.assertTrue(AxisSpec([self.bag, self.bag2], None) == AxisSpec([self.bag, self.bag2], None))

    def test_when_not_same_x_and_y_axes_should_return_false(self):
        self.given_a_board_with_two_bags()

        self.assertFalse(AxisSpec([self.bag], None) == AxisSpec([self.bag2], None))
        self.assertFalse(AxisSpec([self.bag], [self.bag2]) == AxisSpec([self.bag2], [self.bag]))
        self.assertFalse(AxisSpec([self.bag, self.bag2], None) == AxisSpec([self.bag2, self.bag], None))


class AxisSpecParsingBehaviour(TestCase, BoardStepsMixin):
    def test_when_one_bag_named_should_make_it_the_xaxis(self):
        self.given_a_board_with_one_bag()

        result = self.board.parse_axis_spec('bagname')

        self.assertEqual([self.bag], result.x_axis)
        self.assertFalse(result.y_axis)

    def test_when_wrong_name_it_should_explode(self):
        self.given_a_board_with_one_bag()

        with self.assertRaises(AxisSpec.NotValid):
            result = self.board.parse_axis_spec('notbagname')

    def test_when_two_bags_separated_by_plus_should_return_x_and_y_axes(self):
        self.given_a_board_with_three_bags()

        result = self.board.parse_axis_spec('secondbag+thirdbag')

        self.assertEqual([self.bag2], result.x_axis)
        self.assertEqual([self.bag3], result.y_axis)

    def test_when_two_bags_separated_by_comma_should_return_multiple_x_axes(self):
        self.given_a_board_with_two_bags()

        result = self.board.parse_axis_spec('bagname,secondbag')

        self.assertEqual([self.bag, self.bag2], result.x_axis)
        self.assertFalse(result.y_axis)

    def test_when_plus_and_coma_combo_yield_two_axes(self):
        self.given_a_board_with_three_bags()

        result = self.board.parse_axis_spec('bagname+secondbag,thirdbag')

        self.assertEqual([self.bag], result.x_axis)
        self.assertEqual([self.bag2, self.bag3], result.y_axis)

    def test_when_stringified_should_return_spec(self):
        self.given_a_board_with_three_bags()

        result = str(AxisSpec([self.bag], [self.bag2, self.bag3]))

        self.assertEqual('bagname+secondbag,thirdbag', result)

    def test_when_no_y_axis_should_omit_from_spec(self):
        self.given_a_board_with_three_bags()

        result = str(AxisSpec([self.bag, self.bag2], None))

        self.assertEqual('bagname,secondbag', result)

    def test_when_click_specified(self):
        self.given_a_board_with_one_bag()

        result = self.board.parse_axis_spec('bagname;click=edit')

        self.assertEqual([self.bag], result.x_axis)
        self.assertFalse(result.y_axis)
        self.assertEqual('edit', result.click)


class AxisSpecToStringBehaviours(TestCase, BoardStepsMixin):
    def test_when_stringified_should_return_spec(self):
        self.given_a_board_with_three_bags()

        result = str(AxisSpec([self.bag], [self.bag2, self.bag3]))

        self.assertEqual('bagname+secondbag,thirdbag', result)

    def test_when_has_click_should_return_that_too(self):
        self.given_a_board_with_three_bags()

        result = str(AxisSpec([self.bag], [self.bag2, self.bag3], click='edit'))

        self.assertEqual('bagname+secondbag,thirdbag;click=edit', result)


    def test_label_should_use_multiplication_sign(self):
        self.given_a_board_with_three_bags()

        result = AxisSpec([self.bag], [self.bag2, self.bag3]).label()

        self.assertEqual(u'bagname \xD7 secondbag, thirdbag', result)

    def test_when_no_y_axis_should_omit_from_label(self):
        self.given_a_board_with_one_bag()

        result = AxisSpec([self.bag], None).label()

        self.assertEqual('bagname', result)


class AxisTagSetBehaviourts(TestCase, BoardStepsMixin):
    def test_when_one_bag_in_x_axis_should_return_simple_list_o_tags(self):
        self.given_a_one_by_none_axis_spec()

        result = self.axis_spec.x_axis_tag_sets()

        self.assertEqual(set([]), result[0])
        self.assertEqual(set([self.tags[0]]), result[1])
        self.assertEqual(set([self.tags[1]]), result[2])

    def test_when_no_bags_in_y_axis_should_return_list_with_empty_set(self):
        self.given_a_one_by_none_axis_spec()

        result = self.axis_spec.y_axis_tag_sets()

        self.assertEqual([set([])], result)

    def test_when_one_bag_in_y_axis_should_return_simple_list_o_tags(self):
        self.given_a_one_by_one_axis_spec()

        result = self.axis_spec.y_axis_tag_sets()

        self.assertEqual(set([]), result[0])
        self.assertEqual(set([self.tags2[0]]), result[1])
        self.assertEqual(set([self.tags2[1]]), result[2])

class BoardGridOptionsBehaviour(TestCase, BoardStepsMixin):
    def test_when_one_bag_should_it_as_1x0(self):
        self.given_a_board_with_one_bag()

        self.when_asked_for_grid_options()

        self.assertEqual(1, len(self.result))
        self.assertEqual('bagname', str(self.result[0]))

    def test_when_two_bags_return_1x0_and_1x1(self):
        self.given_a_board_with_two_bags()

        self.when_asked_for_grid_options()

        self.assertEqual(2, len(self.result))
        self.assertEqual('bagname', str(self.result[0]))
        self.assertEqual('bagname+secondbag', str(self.result[1]))

    def test_when_three_bags_return_1x0_and_two_1x1s(self):
        self.given_a_board_with_three_bags()

        self.when_asked_for_grid_options()

        self.assertEqual(3, len(self.result))
        self.assertEqual('bagname', str(self.result[0]))
        self.assertEqual('bagname+secondbag', str(self.result[1]))
        self.assertEqual('bagname+thirdbag', str(self.result[2]))

    def when_asked_for_grid_options(self):
        self.result = self.board.grid_options()


class BoardAjaxBehaviour(TestCase, BoardStepsMixin):
    def setUp(self):
        self.client = Client()

    def test_empty_tags_list(self):
        # Inspired by an actual bug
        self.given_a_board_with_one_bag()
        self.given_one_untagged_card()
        self.given_two_tagged_cards()
        self.given_logged_in_as_owner()

        self.when_calling_jarrange(tags=[], order=[self.cards[1], self.cards[0]], dropped=self.cards[1])

        self.assert_successful_json()
        self.assert_card_order([self.cards[1], self.cards[0], self.cards[2]])
        self.assert_card_tags(self.cards[1], [])

    def test_should_replace_tags_and_reorder(self):
        self.given_a_board_with_one_bag()
        self.given_one_untagged_card()
        self.given_two_tagged_cards()
        self.given_logged_in_as_owner()

        self.when_calling_jarrange(tags=[self.tags[0]], order=[self.cards[1], self.cards[0]], dropped=self.cards[1])

        self.assert_successful_json()
        self.assert_card_order([self.cards[1], self.cards[0], self.cards[2]])
        self.assert_card_tags(self.cards[1], [self.tags[0]])

    def assert_successful_json(self):
        self.obj = json.loads(self.response.content)
        self.assertTrue(self.obj['success'])

    def given_one_untagged_card(self):
        if not hasattr(self, 'cards'):
            self.cards = []
        for i in range(1):
            self.cards.append(self.board.card_set.create(
                name='card{0}'.format(len(self.cards)),
                label='card #{0}'.format(len(self.cards))))

    def given_two_tagged_cards(self):
        if not hasattr(self, 'cards'):
            self.cards = []
        for i in range(2):
            self.cards.append(self.board.card_set.create(
                name='card{0}'.format(len(self.cards)),
                label='card #{0}'.format(len(self.cards))))
            self.cards[-1].tag_set.add(self.tags[i])
            self.cards[-1].save()

    def when_calling_jarrange(self, tags, order, dropped):
        self.response = self.client.post('/boards/{0}/grids/bagname/jarrange'.format(self.board.id), {
            u'tags': ','.join(str(t) for t in tags),
            u'order': ' '.join(str(t.id) for t in order),
            u'dropped': str(dropped.id),
        })

    def assert_card_order(self, expected_order):
        actual_order = toposorted(self.board.card_set.all())
        self.assertEqual(expected_order, actual_order)

    def assert_card_tags(self, card, expected_tags):
        actual_tags = list(card.tag_set.all())
        self.assertEqual(expected_tags, actual_tags)




