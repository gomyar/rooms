
from django.conf.urls import include, url

from . views import *


urlpatterns = [
    url(r'^$', index, name='walkabout_index'),
    url(r'^play_game/(?P<game_id>[\w-]+)', play_game, name='walkabout_game'),
    url(r'^playing_games', playing_games, name='walkabout_playing_games'),
    url(r'^available_games', available_games, name='walkabout_available_games'),
    url(r'^create_game', create_game, name='walkabout_create_game'),

    url(r'^join_game', join_game, name='walkabout_join_game'),
    url(r'^player_connects', player_connects, name='walkabout_player_connects'),
]
