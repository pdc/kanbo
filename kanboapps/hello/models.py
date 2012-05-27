# -*-coding: UTF-8-*-

import logging
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from social_auth.models import UserSocialAuth
from social_auth.signals import pre_update, socialauth_registered
from social_auth.backends.contrib.github import GithubBackend
from social_auth.backends.twitter import TwitterBackend

logger = logging.getLogger(__name__)

class Profile(models.Model):
    # This field is required.
    user = models.OneToOneField(User)

    image_url = models.URLField(max_length=400, null=True, blank=True, help_text='User picture for this user.')

    nick = models.CharField(max_length=200)
    image_url = models.URLField(max_length=400, null=True, blank=True, help_text='User picture for this user.')
    created_at = models.DateTimeField(null=True, help_text='When provider reports user was created.')


def create_profile_if_missing(user):
    """Given a user object, return that user’s profile.

    Creates it if it does not already exist."""
    try:
        return user.get_profile()
    except Profile.DoesNotExist:
        logger.debug('Creating profile for {0}'.format(user))
        return Profile.objects.create(user=user)


# Arrange for a user profile to be attached to users on creation.
def on_user_post_save(sender, instance, created, **kwargs):
    #logger.debug('on_user_post_save signal')
    if created:
        profile = Profile.objects.create(user=instance)
    else:
        profile = create_profile_if_missing(instance)
    if hasattr(instance, 'extras'):
        profile = instance.get_profile()
        needs_save = False
        for attr, val in instance.extras:
            if val != getattr(profile, attr, None):
                setattr(profile, attr, val)
                needs_save = True
        if needs_save:
            logger.debug('Updating profile for {0}'.format(instance))
            profile.save()

post_save.connect(on_user_post_save, sender=User)


def on_github_pre_update(sender, user, response, details, **kwargs):
    #logger.debug('on_github_pre_update signal')
    user.extras = [(k, response.get(j)) for (k, j) in [
        ('nick', 'login'),
        ('image_url', 'avatar_url'),
        # ('blog_url', 'blog_url'),
        # ('github_url', 'html_url'),
        # ('location': 'location'),
        ]
    ]
    return True

def on_twitter_pre_update(sender, user, response, details, **kwargs):
    #logger.debug('on_twitter_pre_update signal')
    user.extras = [
        ( 'nick', response.get('screen_name')),
        ( 'image_url', response.get('profile_image_url')),
        ##( 'created_at', datetime.strftime('%a %b %d %H:%M:%S %z %Y', response.get('created_at'))),
    ]
    return True

def on_pre_update(sender, user, response, details, **kwargs):
    logger.debug('on_pre_update signal')
    logger.debug(response)
    return True

def on_socialauth_registration(sender, user, response, details, **kwargs):
    logger.debug('on_socialauth_registration signal')
    user.is_new = True
    return False

pre_update.connect(on_twitter_pre_update, sender=TwitterBackend)
pre_update.connect(on_github_pre_update, sender=GithubBackend)
pre_update.connect(on_pre_update, sender=None)
socialauth_registered.connect(on_socialauth_registration, sender=None)