
from django.conf.urls import patterns, include, url


urlpatterns = patterns('rooms_master.views',
    url(r'^join_game', 'join_game', name='rooms_join_game'),
    url(r'^player_connects', 'player_connects', name='rooms_player_connects'),
)
