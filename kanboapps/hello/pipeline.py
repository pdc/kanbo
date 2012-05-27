# -*-coding: UTF-8-*-

"""Functions for the Django Social Auth pipeline.

This allows us to impose our own rules for usernames.
"""

import re
from uuid import uuid4
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from social_auth.backends.pipeline import USERNAME, USERNAME_MAX_LENGTH

RANDOM_LENGTH = 16

BAD_USERNAME_RE = re.compile(r"""
    -?\d
    """, re.VERBOSE)
url_bits = set([
    'about',
    'hello',
    'boards',
    'api',
    ])
def username_rejected(username):
    """Return true if this username should be rejected

    Reasons for rejection include there already being
    a user with this name.
    """
    return (not username
        or username in url_bits
        or BAD_USERNAME_RE.match(username)
        or User.objects.filter(username=username).exists())

TRICKY_CHARACTERS = {
    0x00C6: u'AE',
    0x00DF: u'ss', # ß
    0x00E6: u'ae',
    0x00D8: 0x004F, # Ø
    0x00F8: 0x006F, # ø
    0x0141: 0x004C, # Ł
    0x0142: 0x006C,  # ł
    0x0152: u'OE', # Œ
    0x0153: u'oe', # œ
}
def slugify_harder(name):
    if isinstance(name, str) :
        name = name.decode('UTF-8')
    name = name.translate(TRICKY_CHARACTERS)
    return slugify(name)


def get_username(details, user=None, user_exists=username_rejected, *args, **kwargs):
    if user: # Existing user?
        return {USERNAME: user.username}

    # New user: create plausible user name suitable for URLs.

    username = details.get(USERNAME, 'user')[:USERNAME_MAX_LENGTH]
    username = slugify_harder(username)

    short_username = username[:USERNAME_MAX_LENGTH-RANDOM_LENGTH]
    while user_exists(username):
        username = short_username + uuid4().hex[:RANDOM_LENGTH]

    return {USERNAME: username}