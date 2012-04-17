KANBO
=====

Every fool is writing their own kanban, Lean, Scrum, etc. task board. Here’s mine.

Status
------

To early to be sure of anything. I have little more than a technology demonstrator for sortable, draggable cards.

Aims
----

- Include only what is strictly needed to make the board.
- Extract maximum flexibility from what is included.
- Don’t let stories that are not stories swamp the board.
- Easy to slice by assignee, by project, etc.

Concepts
--------

Very, very rough

- Stories: Changes to the user-visible behaviour of the system.
- Wants: What the goal donor has said they want done, but not yet in a state that it can be committed to and therefore added to the project backlog.
- Achievements: Stories that have completed their life-cycle.

- Bin (State?): Show where in its life-cycle a story is. Might include project backlog, sprint backlog, in progress, testing, accepted, done, or whatever.
- Tag: Ways of classifying stories. Projects, sprints, etc., might all have tags.
- Bag: A collection of tags. There might be a bag of project tags.
- Bag rules: Says whether a story can have one or many tags from that bag.

The board would be laid out with bins as columns and tags of some bag defining the rows.

Installation
------------

This is a Django web app.

Create a python virtual environment . With virtualenvwrapper, something like this should do the trick:

    mkvirtualenv --python=$(which pypy) --distribute --no-site kanbo

The `--python` option is optional—this server has so far been tested with
Python 2.7 and PyPy 1.8. Either is fine.

One of the packages it uses has to be installed from Git for now:

     pip install git+git://github.com/pdc/fakeredis.git

The rest can be installed in the usual way:

    pip install -r REQUIREMENTS

Now you can test it

    ./manage.py test stories
