import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.conf import settings
from django.http import HttpResponse

from rooms.rpc import WSGIRPCClient


rpc_player = WSGIRPCClient(settings.MASTER_HOST, settings.MASTER_PORT,
    "master_game")
rpc_master = WSGIRPCClient(settings.MASTER_HOST, settings.MASTER_PORT,
    "master_control")


def responsejson(func):
    def call(request, *args, **kwargs):
        return HttpResponse(json.dumps(func(request, *args, **kwargs)),
            content_type="application/json")
    return call


@login_required
def index(request):
    return render_to_response("rooms_demo/index.html",
        dict(username=request.user.username))


@login_required
@responsejson
def playing_games(request):
    return rpc_player.call("all_players_for", username=request.user.username)


@login_required
@responsejson
def managed_games(request):
    return rpc_player.call("all_managed_games_for",
        username=request.user.username)


@login_required
@responsejson
def create_game(request):
    return rpc_player.call("create_game", owner_id=request.user.username)


@login_required
@responsejson
def join_game(request, game_id):
    return rpc_player.call("join_game", username=request.user.username,
        game_id=game_id, **(json.loads(request.body)))


@login_required
@responsejson
def player_connects(request, username, game_id):
    if username != request.user.username:
        raise Exception("Oddness in the API that needs cleaning up")
    return rpc_player.call("player_connects", username=request.user.username,
        game_id=game_id)


@login_required
@responsejson
def game_create_params(request):
    script = rpc_master.call("inspect_script", script_name="player_script")
    player_script = script.get("player_joins", {})
    if player_script:
        return player_script['args'][1:]
    else:
        return dict()
