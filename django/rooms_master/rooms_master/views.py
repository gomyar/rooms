import json

from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.http import HttpResponseBadRequest
from django.conf import settings
from django.contrib.auth.decorators import login_required

from rooms.rpc import WSGIRPCClient


rpc_player = WSGIRPCClient(settings.MASTER_HOST, settings.MASTER_PORT,
    "master_game")
rpc_master = WSGIRPCClient(settings.MASTER_HOST, settings.MASTER_PORT,
    "master_control")


@login_required
def join_game(request):
    if request.method == "POST":
        body = json.loads(request.body)
        game_id = body['game_id']
        alliance_id = body['alliance_id']
        ship_id = body['ship_id']
        node_info = rpc_player.call("join_game", username=request.user.username,
            game_id=game_id, alliance_id=alliance_id, ship_id=ship_id)
        return HttpResponse(json.dumps(node_info),
            content_type="application/json")
    else:
        return HttpResponseBadRequest()


@login_required
def player_connects(request):
    if request.method == "POST":
        game_id = request.POST['game_id']
        node_info = rpc_player.call("player_connects",
            username=request.user.username, game_id=game_id)
        return HttpResponse(json.dumps(node_info),
            content_type="application/json")
    else:
        return HttpResponseBadRequest()
