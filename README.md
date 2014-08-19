KANBO
=====

Every fool is writing their own Kanban, Lean, Scrum, etc. task board. Here’s mine.

Status
------

To early to be sure of anything. I have little more than a technology demonstrator for sortable, draggable cards. A lot of work is required to flash it out in to a real app.

Aims
----

- Include only what is strictly needed to make the board.
- Extract maximum flexibility from what is included.
- Don’t let stories that are not stories swamp the board.
- Easy to slice by assignee, by project, etc.
- Synchronize with your existing task list via a plugin maybe.

Concepts
--------

Very, very roughly, my aim is to have a vague enough set of mechanisms that they can be applied to several flavours of agile development.

- User stories and programmer tasks: Changes to the user-visible behaviour of the system. Stories are  written from the customer’s point of view and are subdivided in to tasks by the programmers when the time comes to implement them.
- Wants: What the goal donor has said they want done, but not yet in a state that it can be committed to and therefore added to the backlog.
- Achievements: Stories that have completed their life-cycle.

The point of separating out wants and achievements is to get them off the board and reduce clutter.

- Card: Represents a story or task on the boad.

- Bin (State?): A place on the board that shows where in its life-cycle a card is. Might include project backlog, sprint backlog, in progress, testing, accepted, done, or whatever.
- Tag: Ways of classifying stories. Projects, sprints, etc., might all be tags.
- Bag: A collection of tags of one type. There might be a bag of project tags.
- Bag rules: Says whether a story can have one or many tags from that bag.

The board would be laid out with bins as columns and tags of some bag defining the rows.

Installation
------------

This is a Django web app.

Create a python virtual environment . With virtualenvwrapper, something like this should do the trick:

    mkvirtualenv --python=$(which pypy) --distribute --no-site kanbo

The `--python` option is optional—this server has so far been tested with
Python 2.7 and a nightly build of PyPy. The latter is fine so long as it works, but can trip over some PyPy bugs, so sticking to CPython will be expedient for now.

One of the packages it uses has to be installed from Git for now:

     pip install git+git://github.com/pdc/fakeredis.git

The rest can be installed in the usual way:

    pip install -r requirements.txt

Now you can test it

    ./manage.py test board

I use South for migrations, so you set up a database as follows

    ./manage.py syncdb
    ./manage.py migrate board


