from django.conf.urls import patterns, include, url

urlpatterns = patterns('rooms_demo.views',
    url(r'^$', 'index', name='rooms_demo_index'),

    url(r'^all_games', 'all_games', name='rooms_all_games'),
    url(r'^playing_games', 'playing_games', name='rooms_playing_games'),
    url(r'^managed_games', 'managed_games', name='rooms_managed_games'),
)
