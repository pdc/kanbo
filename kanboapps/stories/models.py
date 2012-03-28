# -*- coding: UTF-8 -*-

"""Declarations for models used in the stories app.

Thes e models are maintained by South.
After making a change, generate a migration using this command:

    ./manage.py schemamigration  stories --auto

Migrations can be applied using this command:

    ./manage.py migrate stories


"""

import logging
from heapq import heapify, heappop, heappush
from django.db import models

logger = logging.getLogger(__name__)


class Board(models.Model):
    """The universe of stories for one team, or group of teams."""
    label = models.CharField(max_length=200)
    slug = models.SlugField()

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return self.label

    def make_grid(self, columns_def=None):
        stories = toposorted(self.story_set.all())

        if columns_def:
            idss = [[inf['id'] for inf in tag.story_set.values('id')]
                    for tag in  columns_def.tag_set.all()]
            storiess = [[x for x in stories if x.id in ids] for ids in idss]
            missing = [x for x in stories if all(x not in xs for xs in storiess)]
            return [[missing] + storiess]
        return [[stories]]


class Bag(models.Model):
    """A set of tags. One of the axes by which stories are classified."""
    board = models.ForeignKey(Board, null=True)

    name = models.SlugField(max_length=200)
    label = models.CharField(max_length=200)

    def __unicode__(self):
        return self.label


class Tag(models.Model):
    """One of the values of one axis of classification of stories."""
    bag = models.ForeignKey(Bag)

    name = models.SlugField(max_length=200)

    def __unicode__(self):
        return u'{0}:{1}'.format(self.bag.name, self.name)

    class Meta:
        ordering = ['id']


class Story(models.Model):
    """On thing on a board"""
    board = models.ForeignKey(Board)
    tag_set = models.ManyToManyField(Tag, related_name='story_set', blank=True)
    succ = models.ForeignKey('self', null=True, blank=True,
        help_text='Another story that follows this one in the queue.')

    label = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(max_length=2000, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = 'story'
        verbose_name_plural = 'stories'
        ordering = ['created']

    def __unicode__(self):
        return self.label

    def get_tag(self, bag):
        """Get the tag in this bag for this story.

        This best used with exclusive bags.
        """
        return self.tag_set.get(bag=bag)


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
    return list(topoiter(xs))

def topoiter(xs):
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
            # display all the stories than it is to complain
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
                raise CyclesException('Cycles in story succession links of length at least {0}'.format(count))

        n = heappop(queue)
        count -= 1
        yield n.x
        if n.x.succ_id:
            m = n.succ
            m.in_count -= 1
            if not m.in_count:
                heappush(queue, m)

def rearrange_objects(model, ids):
    """Rearrange entities in the model

    Arguments --
        model -- the class defining the universal set of entities
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

    objs_by_id = model.objects.in_bulk(ids)
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
        model.objects.filter(succ__id=i).update(succ=succ_i)

    # Make predecessor of last elt point to start of new order.
    model.objects.filter(succ__id=ids[-1]).update(succ=ids[0])

    # Establish the order amongs the new items.
    for obj, succ in zip(objs, objs[1:]):
        obj.succ = succ
        obj.save()


