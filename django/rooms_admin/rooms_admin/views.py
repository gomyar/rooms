
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
    "player")
rpc_master = WSGIRPCClient(settings.MASTER_HOST, settings.MASTER_PORT,
    "master")


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
def admin_view_area(request, game_id, area_id):
    return render_to_response("admin/admin_view_rooms.html", dict(
        area = master.admin_show_area(game_id=game_id, area_id=area_id),
    ))


@permission_required("is_staff")
def goto_admin(request, game_id, area_id, room_id):
    username = request.user.username
    log.debug("goto_game Player %s connecting", username)
    node_info = master.admin_connects(username=username, game_id=game_id,
        area_id=area_id, room_id=room_id)
    return HttpResponseRedirect(
        "http://%(host)s:%(port)s/admin.html?token=%(token)s" % node_info)


@permission_required("is_staff")
def admin_scripts(request):
    return render_to_response("admin/admin_scripts.html")



@permission_required("is_staff")
@responsejson
def list_scripts(request):
    dirlist = os.listdir(settings.ADMIN_SCRIPT_ROOT)
    return dict(scripts=[f for f in dirlist if f.endswith(".py")],
        chat_scripts=[f for f in dirlist if f.endswith(".json")])

@permission_required("is_staff")
@responsejson
def load_script(request):
    script_file = request.POST['script_file']
    if "/" in script_file:
        raise Exception("Slashes? we dont need no stinkin slashes")
    return open(os.path.join(settings.ADMIN_SCRIPT_ROOT, script_file)).read()

@permission_required("is_staff")
@responsejson
def load_chat_script(request):
    script_file = request.POST['script_file']
    if "/" in script_file:
        raise Exception("Slashes? we dont need no stinkin slashes")
    return open(os.path.join(settings.ADMIN_SCRIPT_ROOT, script_file)).read()

@permission_required("is_staff")
@responsejson
def create_chat_script(request):
    script_file = request.POST['script_file']
    if "/" in script_file:
        raise Exception("Slashes? we dont need no stinkin slashes")
    filepath = os.path.join(settings.ADMIN_SCRIPT_ROOT, script_file)
    if os.path.exists(filepath):
        raise Exception("File already exists")
    newfile = open("%s.json" % (filepath,), "w")
    newfile.write('{ "choices": []}')
    newfile.close()

@permission_required("is_staff")
@responsejson
def save_script(request):
    script_file = request.POST['script_file']
    script_contents = request.POST['script_contents']
    if "/" in script_file:
        raise Exception("Slashes? we dont need no stinkin slashes")
    try:
        script_path = os.path.join(settings.ADMIN_SCRIPT_ROOT, script_file)
        script = open(script_path, "w")
        script.write(script_contents)
        script.close()

        script_name = script_file.rstrip(".py")
        if settings.ADMIN_SCRIPT_ROOT not in sys.path:
            sys.path.append(settings.ADMIN_SCRIPT_ROOT)
        __import__(script_name)
#        reload(_scripts[script_name])
#        for actor in _actor_scripts[script_name]:
#            actor.kick()
        return {'success': True}
    except Exception, e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stacktrace = traceback.format_exception(exc_type, exc_value,
            exc_traceback)
        stacktrace = [str(s) for s in stacktrace]
        stacktrace = "\n".join(stacktrace)
        return {'success': False, 'stacktrace':stacktrace}


@permission_required("is_staff")
@responsejson
def save_chat_script(request):
    script_file = request.POST['script_file']
    script_contents = request.POST['script_contents']
    if "/" in script_file:
        raise Exception("Slashes? we dont need no stinkin slashes")
    try:
        script_path = os.path.join(settings.ADMIN_SCRIPT_ROOT, script_file)
        script = open(script_path, "w")
        script.write(script_contents)
        script.close()

        return {'success': True}
    except Exception, e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stacktrace = traceback.format_exception(exc_type, exc_value,
            exc_traceback)
        stacktrace = [str(s) for s in stacktrace]
        stacktrace = "\n".join(stacktrace)
        return {'success': False, 'stacktrace':stacktrace}


@permission_required("is_staff")
@responsejson
def add_choice(request, chat_script, function, *index):
    script = load_chat_script(chat_script)
    return ""

