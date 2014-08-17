from django.conf.urls import patterns, include, url

urlpatterns = patterns('rooms_demo.views',
    url(r'^$', 'index', name='rooms_demo_index'),

    url(r'^playing_games', 'playing_games', name='rooms_playing_games'),
    url(r'^managed_games', 'managed_games', name='rooms_managed_games'),
    url(r'^available_games', 'available_games', name='rooms_available_games'),

    url(r'^create_game', 'create_game', name='rooms_create_game'),

    url(r'^game_create_params', 'game_create_params',
        name='rooms_game_create_params'),

    url(r'^join_game/(?P<game_id>.*)', 'join_game', name='rooms_join_game'),
    url(r'^player_connects/(?P<username>.*)/(?P<game_id>.*)', 'player_connects', name='rooms_player_connects'),
)
