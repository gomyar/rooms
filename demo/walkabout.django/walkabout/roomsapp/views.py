import json

from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings

from rooms.rpc import WSGIRPCClient


rpc_rooms = WSGIRPCClient(settings.ROOMS_HOST, "master")


def responsejson(func):
    def call(request, *args, **kwargs):
        return HttpResponse(json.dumps(func(request, *args, **kwargs)),
            content_type="application/json")
    return call


@login_required
@require_http_methods(['GET'])
def index(request):
    return render(request, "walkabout/index.html", dict(user=request.user))


@login_required
@require_http_methods(['GET'])
def play_game(request, game_id):
    return render(request, "walkabout/game.html", dict(user=request.user,
                                                       game_id=game_id))


@login_required
@require_http_methods(['GET'])
@responsejson
def playing_games(request):
    return rpc_rooms.call("list_players", username=request.user.username)


@login_required
@require_http_methods(['GET'])
@responsejson
def available_games(request):
    players = rpc_rooms.call("list_players", username=request.user.username)
    playing_games = [player['game_id'] for player in players]
    all_games = rpc_rooms.call("list_games")
    avail_games = [game for game in all_games if game['game_id'] not \
        in playing_games]
    return avail_games


@login_required
@require_http_methods(['POST'])
@responsejson
def create_game(request):
    game_id = rpc_rooms.call("create_game",
                             owner_username=request.user.username)
    return game_id


@login_required
@require_http_methods(['POST'])
@responsejson
def join_game(request):
    node_info = rpc_rooms.call("join_game", username=request.user.username,
        game_id=request.POST['game_id'])
    return node_info


@login_required
@require_http_methods(['POST'])
@responsejson
def player_connects(request):
    game_id = request.POST['game_id']
    node_info = rpc_rooms.call("player_connects",
        username=request.user.username, game_id=game_id)
    return node_info
