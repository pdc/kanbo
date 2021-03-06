# Django settings for kanbo project.

import os, sys

project_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
def local_path(path):
    return os.path.join(project_dir, path)

if project_dir not in sys.path:
    sys.path[1:1] = [project_dir]

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': local_path('dev.db'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

EVENT_REPEATER = {
    'ENGINE': ('fakeredis.FakeRedis' if 'test' in sys.argv else 'redis.Redis'),
    'PARAMS': {
        'db': 0,
    },
    'TTL': 120,
    'INTERVAL_SECONDS': 5,
    'POLL': True,
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-GB'

# SITE_ID = 1

# How to refer to this version of the site in mail etc.
SITE_NAME = os.environ.get('SITE_NAME', 'Kanbo (dev)')

# How to make absolute URLs for links to this version of the site
SITE_ORIGIN = os.environ.get('SITE_ORIGIN', 'http://localhost:8000')

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True


# FIXME This needs to be replaced with a dfifferent way to do profiles
AUTH_PROFILE_MODULE = 'hello.Profile'

# Used by django-social-auth to log people in.
# See http://django-social-auth.readthedocs.org/en/latest/configuration.html
AUTHENTICATION_BACKENDS = (
    'social_auth.backends.twitter.TwitterBackend',
    ##'social_auth.backends.facebook.FacebookBackend',
    ##'social_auth.backends.google.GoogleOAuthBackend',
    ##'social_auth.backends.google.GoogleOAuth2Backend',
    ##'social_auth.backends.google.GoogleBackend',
    ##'social_auth.backends.yahoo.YahooBackend',
    ##'social_auth.backends.browserid.BrowserIDBackend',
    ##'social_auth.backends.contrib.linkedin.LinkedinBackend',
    ##'social_auth.backends.contrib.livejournal.LiveJournalBackend',
    ##'social_auth.backends.contrib.orkut.OrkutBackend',
    ##'social_auth.backends.contrib.foursquare.FoursquareBackend',
    'social_auth.backends.contrib.github.GithubBackend',
    ##'social_auth.backends.contrib.vkontakte.VkontakteBackend',
    ##'social_auth.backends.contrib.live.LiveBackend',
    ##'social_auth.backends.contrib.skyrock.SkyrockBackend',
    ##'social_auth.backends.contrib.yahoo.YahooOAuthBackend',
    ##'social_auth.backends.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_PIPELINE = (
    'social_auth.backends.pipeline.social.social_auth_user',
    'social_auth.backends.pipeline.associate.associate_by_email',
    'kanbo.hello.pipeline.get_username',
    'social_auth.backends.pipeline.user.create_user',
    'social_auth.backends.pipeline.social.associate_user',
    'social_auth.backends.pipeline.social.load_extra_data',
    'social_auth.backends.pipeline.user.update_user_details'
)

# Customization for supported backends.
TWITTER_CONSUMER_KEY = 'TK6vDXLBmmCDdYiWrBtrw'
TWITTER_CONSUMER_SECRET = 'JykUbMOUmWnCgF9ChROMy7UFo62bxjHIWQhwdaKTc'
GITHUB_APP_ID = 'e99319e4aee02e64ec19'
GITHUB_API_SECRET = '4c2febde0e198e6ab712c81a1261890f3d25ea70'
##GITHUB_EXTENDED_PERMISSIONS = [...]

LOGIN_URL = '/hello/login-form'
LOGIN_REDIRECT_URL = '/hello/logged-in'
LOGIN_ERROR_URL    = '/hello/login-error'
##SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/hello/logged-in'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/hello/create-user'
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = '/hello/create-association'
SOCIAL_AUTH_DISCONNECT_REDIRECT_URL = '/hello/delete-association'
##SOCIAL_AUTH_BACKEND_ERROR_URL = '/hello/problem'

SOCIAL_AUTH_COMPLETE_URL_NAME  = 'socialauth_complete'
SOCIAL_AUTH_ASSOCIATE_URL_NAME = 'socialauth_associate_complete'

SOCIAL_AUTH_DEFAULT_USERNAME = 'boffo'
SOCIAL_AUTH_EXPIRATION = 'expires'
# There are other more exotic sewttings listed at
# <http://django-social-auth.readthedocs.org/en/latest/configuration.html>

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/home/kanbo/static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = 'http://static.kanbo.me.uk/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '{0}admin/'.format(STATIC_URL)

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    local_path('static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'jgk9*=7lngzz1bje0t^_#=^gt*ph*2!339!l9=&ji*$go-v71c'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'social_auth.context_processors.social_auth_by_name_backends',
    'social_auth.context_processors.social_auth_backends',
    'social_auth.context_processors.social_auth_login_redirect',
    ##'social_auth.context_processors.social_auth_by_type_backends',
    'kanbo.hello.context_processors.profile',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'kanbo.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    local_path('templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'south',
    'social_auth',

    'kanbo.board',
    'kanbo.about',
    'kanbo.hello',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
