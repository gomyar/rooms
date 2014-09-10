
import os
import sys
import traceback
import json

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth.decorators import permission_required
from django.conf import settings

from rooms.rpc import WSGIRPCClient

import logging
log = logging.getLogger("rooms.admin")

rpc_player = WSGIRPCClient(settings.MASTER_HOST, settings.MASTER_PORT,
    "master_game")
rpc_master = WSGIRPCClient(settings.MASTER_HOST, settings.MASTER_PORT,
    "master_control")


def responsejson(func):
    def call(request, *args, **kwargs):
        return HttpResponse(json.dumps(func(request, *args, **kwargs)))
    return call


@permission_required("is_staff")
def index(request):
    return render_to_response("rooms_admin/index.html")


@permission_required("is_staff")
@responsejson
def all_nodes(request):
    return rpc_master.call("all_nodes")


@permission_required("is_staff")
@responsejson
def all_rooms_on_node(request, host, port):
    rpc = WSGIRPCClient(host, port, "node_control")
    return rpc.call("all_rooms")


@permission_required("is_staff")
@responsejson
def request_admin_token(request):
    param = json.loads(request.body)
    game_id = param['game_id']
    room_id = param['room_id']
    return rpc_master.call("request_admin_token", game_id=game_id,
        room_id=room_id)


@permission_required("is_staff")
@responsejson
def save_item(request):
    params = json.loads(request.body)
    for param in params:
        category = param.pop('category')
        item_type = param.pop('item_type')
    return rpc_master.call("save_item", category=category, item_type=item_type,
        **param)


@permission_required("is_staff")
@responsejson
def all_items(request):
    return rpc_master.call("all_items")
