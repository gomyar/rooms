
from django.conf.urls import include, url

from . views import *


urlpatterns = [
    url(r'^playing_games', playing_games, name='rooms_api_playing_games'),
    url(r'^available_games', available_games, name='rooms_api_available_games'),
    url(r'^create_game', create_game, name='rooms_api_create_game'),

    url(r'^join_game', join_game, name='rooms_api_join_game'),
    url(r'^player_connects', player_connects, name='rooms_api_player_connects'),
]
