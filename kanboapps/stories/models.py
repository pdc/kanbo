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

    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateField(auto_now=True, editable=False)

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

    created = models.DateField(auto_now_add=True, editable=False)
    modified = models.DateField(auto_now=True, editable=False)

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


def rearrange(model, ids):
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
    skips[ids[-1]] = ids[0]

    # Reduce the list by eliminating chains within our ordered elements.
    # Varient: len(skips)
    while skips:
        for i, succ_i in skips.items():
            if succ_i == ids[0]:
                continue
            succ_succ_i = skips.get(succ_i)
            if succ_succ_i:
                del skips[succ_i]
                skips[i] = succ_succ_i
                break
        else:
            break
    after = None
    for i, succ_i in skips.items():
        if succ_i == ids[0]:
            after = i, succ_i
        else:
            model.objects.filter(succ__id=i).update(succ=succ_i)
    if after:
        # The alteration linking to the start has to go after the rest
        # to avoid creating stoopid cycles.
        i, succ_i = after
        model.objects.filter(succ__id=i).update(succ=succ_i)

    # Establish the order amongs the new items.
    for obj, succ in zip(objs, objs[1:]):
        obj.succ = succ
        obj.save()


