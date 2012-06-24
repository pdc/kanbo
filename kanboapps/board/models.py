# -*- coding: UTF-8 -*-

"""Declarations for models used in the board app.

These models are maintained by South.
After making a change, generate a migration using this command:

    ./manage.py schemamigration  board --auto

Migrations can be applied using this command:

    ./manage.py migrate board

This module also includes some functions and classes
that operate on the model instances.

"""

import sys
import logging
import re
from heapq import heapify, heappop, heappush
import redis
import json
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class AxisSpec(object):
    """Specifies the axes of the grid.

    Not stored in the db: used to represent
    part of the URL of grid pages.
    """

    class NotValid(ValueError):
        """Raised when cannot parse an axis spec."""
        def __init__(self, bad_spec):
            super(AxisSpec.NotValid, self).__init__('{0}: not a valid axis spec'.format(bad_spec))

    def __init__(self, x_axis, y_axis):
        self.x_axis = x_axis
        self.y_axis = y_axis

    def x_axis_tag_sets(self):
        """A list of sets, each containing tags from the bags in the axis."""
        return self.axis_tag_sets(self.x_axis)

    def y_axis_tag_sets(self):
        """A list of sets, each containing tags from the bags in the axis."""
        return self.axis_tag_sets(self.y_axis)

    def axis_tag_sets(self, axis):
        if not axis:
            return [set()]
        return [set()] + [set([t]) for t in axis[0].tags_sorted()]

    def __str__(self):
        if not self.y_axis:
            return  ','.join(b.name for b in self.x_axis)
        return '{0}+{1}'.format(
            ','.join(b.name for b in self.x_axis),
            ','.join(b.name for b in self.y_axis))


class Grid(object):
    """Represents a 2d presentation of cards.

    Not stored in the db, but constructed on demand.
    """
    def __init__(self, rows):
        self.rows = rows

    def __eq__(self, other):
        return self.rows == other.rows

    def __str__(self):
        return '[%s]' % '\n  '.join(str(r) for r in self.rows)

    def __repr__(self):
        return 'Grid({0!r})'.format(self.rows)


class GridRow(object):
    def __init__(self, bins, tags=None):
        self.bins = bins
        self.tags = tags

    def __eq__(self, other):
        return self.tags == other.tags and self.bins == other.bins

    def __str__(self):
        return ' | '.join(str(b) for b in self.bins)

    def __repr__(self):
        return 'GridRow({0!r}, tags={1!r})'.format(self.bins, self.tags)


class GridBin(object):
    def __init__(self, cards, tags=None):
        self.cards = cards
        self.tags = set(tags or [])

        self.element_id =  ('bin-' + '-'.join(str(x.id) for x in self.tags)
                if tags else 'untagged-bin')

    def __eq__(self, other):
        return (self.tags == other.tags
            and len(self.cards) == len(other.cards)
            and all(x.id == y.id for (x, y) in zip(self.cards, other.cards)))

    def __str__(self):
        return ', '.join(c.name for c in self.cards)

    def __repr__(self):
        return 'GridBin({0!r}, tags={1!r})'.format(self.cards, self.tags)


lowercase_validator = RegexValidator(re.compile(r'^[a-z\d-]+$'), 'Must be lower-case letters a-z, digits, or hyphens')
class KeywordValidator(object):
    def __init__(self, ws):
        self.words = set(ws)

    def __call__(self, value):
        if value in self.words:
            raise ValidationError(u'The name \u2018{0}\u2019 is reserved and cannot be used.'.format(value))

board_level_keywords = ['new', 'create', 'edit', 'update', 'delete', 'profile', 'kanbo']


class Board(models.Model):
    """The universe of cards for one team, or group of teams."""
    owner = models.ForeignKey(User)
    collaborators = models.ManyToManyField(User, through='Access',
            related_name='board_access_set',
            blank=True,
            help_text='People who have been given access to this board (part from the owner).')

    name = models.CharField(max_length=50, db_index=True,
        validators=[lowercase_validator, KeywordValidator(board_level_keywords)],
        verbose_name='Short name',
        help_text='The unique short name for this board. Used to make the URL for the board. Lowercase letters, digits, and dashes only.')
    label = models.CharField(max_length=200,
        blank=True,
        verbose_name='Display name',
        help_text='The human-readable name or one-line description for your board. Blank means use the short name.')
    is_public = models.BooleanField(default=False,
        verbose_name='Public board',
        help_text='Allows anyone at all to add or rearrange cards.')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = (('owner', 'name'),)

    def __unicode__(self):
        return self.label

    @models.permalink
    def get_absolute_url(self):
        """Returns the canonical link to this board."""
        return 'card-grid', (), {
            'owner_username': self.owner.username,
            'board_name': self.name,
            'axes': self.bag_set.all()[0].name,
        }

    @models.permalink
    def get_detail_url(self):
        return 'board-detail', (), {
            'owner_username': self.owner.username,
            'board_name': self.name,
        }

    def clean(self):
        """Called as part of validating a form creating an instance of this model."""
        super(Board, self).clean()
        if Board.objects.filter(owner=self.owner, name=self.name
                ).exclude(id=self.id).exists():
            raise ValidationError('You already have a board named ‘{0}’.'.format(self.name))

    def allows_rearrange(self, user):
        if self.is_public:
            return True
        if not user.is_authenticated():
            return False
        if user == self.owner:
            return True
        try:
            access = Access.objects.get(user=user, board=self)
            return access.can_rearrange
        except Access.DoesNotExist:
            return False
        return False

    allows_add_card = allows_rearrange

    def allows_add_remove_user(self, user):
        if self.is_public:
            return False # Can’t add users because everyone is invited.
        if not user.is_authenticated():
            return False
        if user == self.owner:
            return True
        return False

    def make_grid(self, axis_spec):
        """Arrange the cards in to a grid as specified by the axis spec.

        Returns an instance of class Grid.
        """
        cards = toposorted(self.card_set.all())

        # Find the labels for the columns and rows.
        xss = axis_spec.x_axis_tag_sets()[1:]
        yss = axis_spec.y_axis_tag_sets()[1:]

        # Get map from tags to card IDs.
        all_tags = set(x for xs in xss for x in xs) | set(y for ys in yss for y in ys)
        ids_by_tag = dict((tag, [inf['id'] for inf in tag.card_set.values('id')])
            for tag in  all_tags)

        # Now get the card ID sets for columns and rows
        xcardidss = [intersection(ids_by_tag[t] for t in xs) for xs in xss]
        ycardidss = [intersection(ids_by_tag[t] for t in ys) for ys in yss]

        # Now the ‘core’ bins want the cards n the intersection of sets
        binss = [
            [GridBin([c for c in cards if c.id in xcardids and c.id in ycardids], xs | ys)
                for (xs, xcardids) in zip(xss, xcardidss)]
            for (ys, ycardids) in zip(yss, ycardidss)]

        # Top row is bins with no y-axis tag.
        xmissings = [
            GridBin([c for c in cards if c.id in xcardids and all(c not in bs[i].cards for bs in binss)], xs)
            for (i, (xs, xcardids)) in enumerate(zip(xss, xcardidss))]
        # Left row is bins with no x-axis tag
        ymissings = [
            GridBin([c for c in cards if c.id in ycardids and all(c not in b.cards for b in bs)], ys)
            for (ys, ycardids, bs) in zip(yss, ycardidss, binss)]

        # Top left corner is bin for cards with no x- or y-axis tags.
        # When no axes are defined, this will be all the cards!
        missing = GridBin([c for c in cards if not any(c.id in ids for ids in ids_by_tag.values())], set())

        return Grid(
            [GridRow([missing] + xmissings)]
            + [GridRow([ymissing] + bs) for (ymissing, bs) in zip(ymissings, binss)])

    def event_stream(self):
        """Return the event stream for this board."""
        return EventRepeater().get_stream(self.id)

    def parse_axis_spec(self, spec):
        """Given a string return an axis spec.

        Axis spec is used later to generate a grid.

        <axis spec> ::= <empty> | <one axis> ( ‘+’ <one axis> )?
        <one axis> ::= <bag name> ( ‘,’ <bag name> )*
        """
        parts = spec.split('+')
        try:
            x_axis = [self.bag_set.get(name=n) for n in parts[0].split(',')]
            y_axis = ([self.bag_set.get(name=n) for n in parts[1].split(',')]
                    if len(parts) > 1
                    else None)
        except Bag.DoesNotExist, e:
            raise AxisSpec.NotValid(spec)

        return AxisSpec(x_axis, y_axis)



def intersection(xss):
    it = iter(xss)
    try:
        xs0 = next(it)
        return set(x for x in xs0 if all(x in xs for xs in it))
    except StopIteration:
        return set()


class Access(models.Model):
    """Links a user to a board they have been given access to."""
    user = models.ForeignKey(User)
    board = models.ForeignKey(Board)

    can_rearrange = models.BooleanField(default=True, help_text='Can this user rearrange the cards on this board?')

    joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'board')]

    def __unicode__(self):
        return u'{0}/{1}–{2}'.format(self.board.owner.username, self.board.name, self.user.username)


class Bag(models.Model):
    """A set of tags. One of the axes by which cards are classified."""
    board = models.ForeignKey(Board, null=True)

    name = models.SlugField(db_index=True, max_length=200,
        validators=[lowercase_validator],
        help_text='Uniquely identifies this bag in the scope of its board. Used in URLs. Consists of letters, digits, and dashes only (no spaces).')

    class Meta:
        unique_together = [('board', 'name')]

    def __unicode__(self):
        return self.name

    def allows_rearrange(self, user):
        return self.board.allows_rearrange(user)

    def allows_delete(self, user):
        return user == self.board.owner

    @models.permalink
    def get_absolute_url(self):
        return 'bag-detail', (), {
            'owner_username': self.board.owner.username,
            'board_name': self.board.name,
            'bag_name': self.name,
        }

    @models.permalink
    def get_new_tag_url(self):
        return 'new-tag', (), {
            'owner_username': self.board.owner.username,
            'board_name': self.board.name,
            'bag_name': self.name,
        }

    def tags_sorted(self):
        """A list of tag objects."""
        return toposorted(self.tag_set.all())




class Tag(models.Model):
    """One of the values of one axis of classification of cards."""
    bag = models.ForeignKey(Bag)
    succ = models.ForeignKey('self', null=True, blank=True,
        help_text='Another tag that follows this one in conventional order')

    name = models.SlugField(max_length=200,
        validators=[lowercase_validator],
        help_text='Uniquely identifies this tag in the scope of its bag. Consists of letters, digits, and dashes only (no spaces).')

    class Meta:
        ordering = ['id']
        unique_together = [('bag', 'name')]

    def __unicode__(self):
        return u'{0}:{1}'.format(self.bag.name, self.name)

    def clean(self):
        """Called as part of validating a form creating an instance of this model."""
        super(Tag, self).clean()
        if Tag.objects.filter(bag=self.bag, name=self.name
                ).exclude(id=self.id).exists():
            raise ValidationError('You already have a {0} tag ‘{1}’.'.format(self.bag.name, self.name))


class Card(models.Model):
    """On thing on a board"""
    board = models.ForeignKey(Board)
    tag_set = models.ManyToManyField(Tag, related_name='card_set', blank=True)
    succ = models.ForeignKey('self', null=True, blank=True,
        help_text='Another card that follows this one in the queue.')

    name = models.SlugField(verbose_name='Short name', help_text='Short code or number that uniquely identifies this card')
    label = models.CharField(max_length=200, help_text='The sentence or phrase written on the card')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ['created']
        unique_together=[('board', 'name')]

    def __unicode__(self):
        return self.label

    def get_tag(self, bag):
        """Get the tag in this bag for this card.

        This best used with exclusive bags.
        """
        return self.tag_set.get(bag=bag)

    def replace_tags(self, axes, tags):
        """Add the tags to this card, removing any from maching bags."""
        for old_tag in self.tag_set.filter(bag__in=axes):
            self.tag_set.remove(old_tag)
        for tag in tags:
            self.tag_set.add(tag)


class CyclesException(Exception):
    pass

def toposort(xs):
    """Given a list of things with a partial order, sort them.

    Things have  id and  succ_id attributes.
    The id is unique. All id values are non-false
    (i.e., not zero, empty string, None)

    succ_id identfies a thing that goes after x.
    A false value for succ_id means x has no successor.

    Permute the list so that each x preceeds its successor
    (the thing with id==x.succ_id).

    Note that xs is sorted in place. As with sort, there is no return value.
    """
    xs[:] = topoiter(xs)

def toposorted(xs):
    """Given a list of things with a partial order, return a sorted list.

    Things have  id and  succ_id attributes.
    The id is unique. All id values are non-false
    (i.e., not zero, empty string, None)

    succ_id identfies a thing that goes after x.
    A false value for succ_id means x has no successor.

    Permute the list so that each x preceeds its successor
    (the thing with id==x.succ_id).

    This returns a fresh list.
    """
    return list(topoiter(xs))

def topoiter(xs):
    """Given a list of things with a partial order, yield the things in order.

    Things have  id and  succ_id attributes.
    The id is unique. All id values are non-false
    (i.e., not zero, empty string, None)

    succ_id identfies a thing that goes after x.
    A false value for succ_id means x has no successor.

    Permute the list so that each x preceeds its successor
    (the thing with id==x.succ_id).

    This is a generator, and yields the things in order.
    """
    # Here’s one traditional algorith for the general case.
    # We are hoping to simplify based on a simplified graph
    # where each node has at most one outgoing edge.
    #
    # L ← Empty list that will contain the sorted elements
    # S ← Set of all nodes with no incoming edges
    # while S is non-empty do
    #     remove a node n from S
    #     insert n into L
    #     for each node m with an edge e from n to m do
    #         remove edge e from the graph
    #         if m has no other incoming edges then
    #             insert m into S
    # if graph has edges then
    #     return error (graph has at least one cycle)
    # else
    #     return L (a topologically sorted order)

    class Node(object):
        __slots__ = ('x', 'index', 'succ', 'in_count')
        def __init__(self, x, index):
            self.x = x
            self.index = index
            self.in_count = 0

        def __str__(self):
            return str(x)

        def __repr__(self):
            return 'Node({0!r})'.format(self.x)

        def __le__(self, other):
            return self.index <= other.index

    nodes = [Node(x, i) for (i, x) in enumerate(xs)]
    nodes_by_id = dict((n.x.id,n) for n in nodes)
    for n in nodes:
        if n.x.succ_id:
            n.succ = nodes_by_id[n.x.succ_id]
            n.succ.in_count += 1

    queue = [n for n in nodes if not n.in_count]
    count = len(nodes)
    while count:
        if not(queue):
            # This shows there are one or more cycles in the input.
            # For our purposes it is more important to
            # display all the cards than it is to complain
            # about cycles. (But they should never happen.)
            for n in nodes:
                if n.in_count:
                    # this is a candidate for disentanglement
                    logger.warn('Breaking cycle during topoiter: changing {0} in-count from {1} to 0'.format(n.x, n.in_count))
                    n.in_count = 0
                    queue = [n]
                    break
                else:
                    pass
            else:
                # None fond. Probably a bug.
                raise CyclesException('Cycles in card succession links of length at least {0}'.format(count))

        n = heappop(queue)
        count -= 1
        yield n.x
        if n.x.succ_id:
            m = n.succ
            m.in_count -= 1
            if not m.in_count:
                heappush(queue, m)

def rearrange_objects(queryset, ids):
    """Rearrange entities in the model

    Arguments --
        queryset -- the universal set of entities
        ids -- identifies some subset of the entities and
            specifies the desired order of them relative to each other

    The ids argument can be a subset of the entire
    collection of model instances, or all of them.

    The effect should be that the items are now in the
    specified order, and occupy the position in the overall
    ordering that the last item in the sequence once did.
    """
    if not ids or len(ids) == 1:
        # Nothing to do.
        return

    objs_by_id = queryset.in_bulk(ids)
    objs = [(objs_by_id[i] if i else None)for i in ids]

    # We will insert the new sequence
    # where the new FINAL item originally sat.
    # Start by plucking all the others out of
    # the established partial order.
    # We do this by setting the successor of
    # their predecessors to their successors.

    # Create a  list of succ relationships
    # we need to patch over.
    skips = dict((x.id, x.succ.id if x.succ else None) for x in objs[:-1])


    # Reduce the list by eliminating chains within our ordered elements.
    # Variant: len(skips)
    while skips:
        for i, succ_i in skips.items():
            if i == succ_i:
                # This happens if there are cycles within our items.
                skips[i] = 0 # Break the cycle
                break
            if succ_i in skips:
                succ2_i = skips[succ_i]
                skips[i] = succ2_i
                del skips[succ_i]
                break
        else:
            break
    for i, succ_i in skips.items():
        queryset.filter(succ__id=i).update(succ=succ_i)

    # Make predecessor of last elt point to start of new order.
    queryset.filter(succ__id=ids[-1]).update(succ=ids[0])

    # Establish the order amongs the new items.
    for obj, succ in zip(objs, objs[1:]):
        obj.succ = succ
        obj.save()


_redis_class = None
def get_redis():
    global _redis_class
    if _redis_class is None:
        module_name, class_name = settings.EVENT_REPEATER['ENGINE'].rsplit('.', 1)
        module = __import__(module_name, globals(), locals(), [class_name])
        _redis_class = getattr(module, class_name)
    return _redis_class(**settings.EVENT_REPEATER['PARAMS'])

class EventsExpired(Exception):
    pass

class EventRepeater(object):
    def __init__(self):
        self.redis = get_redis()

    def get_stream(self, id):
        return EventStream(self, id)


class EventStream(object):
    """Accepts events and repeats them when polled."""

    def __init__(self, owner, id):
        """Create a repeater with this ID."""
        self.owner = owner
        self.redis = owner.redis
        self.id = id
        self.k_info = 'kanbo:ev:{0}:info'.format(self.id)
        self.k_list = 'kanbo:ev:{0}:list'.format(self.id)

    def next_seq(self):
        x = self.redis.hget(self.k_info, 'next')
        return (int(x) if x else 0)

    def append(self, event):
        jevent = json.dumps(event)
        def try_append(p):
            next_seq = p.hget(self.k_info, 'next') or 0
            len_evs = p.llen(self.k_list)

            p.multi()
            if not len_evs:
                p.hset(self.k_info, 'start', next_seq)
            p.hincrby(self.k_info, 'next', 1)
            p.rpush(self.k_list, jevent)
            p.expire(self.k_list, settings.EVENT_REPEATER['TTL'])
        self.redis.transaction(try_append, self.k_info, self.k_list)

    def as_json_starting_from(self, seq):
        # As a transaction in case events arrive while
        # we are calculating the boundaries of the range.
        result = [None, None]
        def try_transaction(p):
            next_str = p.hget(self.k_info, 'next')
            next = (int(next_str) if next_str else 0)
            result[1] = next
            if p.exists(self.k_list):
                start_str = p.hget(self.k_info, 'start')
                start = (int(start_str) if start_str else 0)
            else:
                start = next
            if seq < start:
                raise EventsExpired('{0}: events expired'.format(seq))
            p.multi()
            p.lrange(self.k_list, seq - start, -1)

        jevs, = self.redis.transaction(try_transaction,  self.k_info, self.k_list)
        result[0] = '[{0}]'.format(', '.join(jevs))
        return tuple(result)