from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('apps.stories.views',
    url(r'^$', 'board_list', name='board_list'),
    url(r'^(?P<board_id>\d+)$', 'story_list', name='story_list'),
)
