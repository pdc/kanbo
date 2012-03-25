# -*- coding: UTF-8 -*-

"""Declarations for models used in the stories app."""

from django.db import models


class Bag(models.Model):
    name = models.SlugField(max_length=200)
    label = models.CharField(max_length=200)

    def __unicode__(self):
        return self.label


class Tag(models.Model):
    bag = models.ForeignKey(Bag)

    name = models.SlugField(max_length=200)

    def __unicode__(self):
        return u'{0}:{1}'.format(self.bag.name, self.name)


class Board(models.Model):
    """The universe of stories for one team, or group of teams."""
    label = models.CharField(max_length=200)
    slug = models.SlugField()

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return self.label


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
        __slots__ = ('x', 'succ', 'in_count')
        def __init__(self, x):
            self.x = x
            self.in_count = 0

    nodes = [Node(x) for x in xs]
    nodes_by_id = dict((n.x.id,n) for n in nodes)
    for n in nodes:
        if n.x.succ_id:
            n.succ = nodes_by_id[n.x.succ_id]
            n.succ.in_count += 1

    ns = [n for n in nodes if not n.in_count]
    count = 0
    while ns:
        n = ns.pop(0)
        count += 1
        yield n.x
        if n.x.succ_id:
            m = n.succ
            m.in_count -= 1
            if not m.in_count:
                ns.append(m)
    if count < len(xs):
        raise CyclesException('Cycles in story succession links')
