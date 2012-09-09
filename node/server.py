#!/usr/bin/env python

import eventlet
eventlet.monkey_patch()

from eventlet import wsgi
from eventlet import websocket
from eventlet import backdoor

import time
import os

from optparse import OptionParser

import xmlrpclib

import uuid

import urlparse
from mimetypes import guess_type

import simplejson

from rooms.instance import Instance
from rooms.admin import Admin

from eventlet.queue import Empty

from container import init_mongo

import signal
import sys


import logging
import logging.config
logging.config.fileConfig("logging.conf")
log = logging.getLogger("rooms.node")

instances = dict()
sessions = dict()

master = None
master_addr = None
game_root = None

def _read_cookies(environ):
    cookie_str = environ['HTTP_COOKIE']
    cookies = cookie_str.split(';')
    cookies = map(lambda c: c.strip().split('='), cookies)
    return dict(cookies)


qcount = 1


def checked(func):
    def tryexcept(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            log.exception("Exception calling %s", func)
            raise
    return tryexcept


@checked
@websocket.WebSocketWSGI
def handle_socket(ws):
    player_id = None
    instance = None
    queue = None
    try:
        cookies = _read_cookies(ws.environ)
        player_id = ws.wait()
        instance_uid = ws.wait()
        instance = instances[instance_uid]
        log.debug("registering %s at %s", player_id, instance_uid)
        queue = instance.connect(player_id)
        log.debug("Connected to queue")
        sessions[cookies['sessionid']] = player_id
        log.debug("Sending sync")
        instance.send_sync(player_id)
        log.debug("Sync sent")
        connected = True
        while not ws.websocket_closed and connected:
            try:
                command = queue.get(timeout=5)
                commands = [ command ]
                if command['command'] == "disconnect":
                    connected = False
                while queue.qsize() > 0:
                    if command['command'] == "disconnect":
                        connected = False
                    command = queue.get()
                    commands.append(command)
                dumps = simplejson.dumps(commands)
                ws.send(dumps)
            except Empty, err:
                ws.send(simplejson.dumps([{'command':"heartbeat"}]))
    except:
        log.exception("Websocket disconnected %s", player_id)
    finally:
        log.debug("Player %s disconnecting", player_id)
        if instance and queue:
            instance.disconnect_queue(queue)


@checked
def game_handle(environ, response):
    _, url, instance_uid, actor_id, command = \
        environ['PATH_INFO'].split("/")
    log.debug("Game call %s, %s, %s, %s", url, instance_uid, actor_id,
        command)
    cookies = _read_cookies(environ)
    params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
    instance = instances[instance_uid]
    returned = instance.call(command, sessions[cookies['sessionid']],
        actor_id, dict(params))
    if returned:
        returned = simplejson.dumps(returned)
    else:
        returned = "[]"
    response('200 OK', [
        ('content-type', 'text/javascript'),
        ('content-length', len(returned)),
    ])
    return returned


@checked
def control_handle(environ, response):
    path = environ['PATH_INFO'].replace("/control/", "")
    params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))

    returned = ""

    if path == "player_joins":
        instance_uid = params['instance_uid']
        player_id = params['player_id']
        instance = instances[instance_uid]
        instance.register(player_id)
        returned = '{"success":true}'
        log.info("Player %s joined instance %s", player_id, instance_uid)

    if path == "create_instance":
        map_id = params['map_id']
        uid = str(uuid.uuid1())
        instance = Instance(uid, master)
        instance.load_map(map_id)
        instances[uid] = instance
        instance.kickoff()
        returned = '{"instance_uid": "%s"}' % (uid,)
        log.info("Instance created %s : %s", map_id, uid)

    response('200 OK', [
        ('content-type', 'text/javascript'),
        ('content-length', len(returned)),
    ])
    return returned


@checked
def room_handle(environ, response):
    _, url, instance_uid = environ['PATH_INFO'].split("/")
    log.debug("Room call: %s %s", url, instance_uid)
    cookies = _read_cookies(environ)
    instance = instances[instance_uid]
    returned = instance.players[sessions[cookies['sessionid']]]['player'].\
        room.external()
    if returned:
        returned = simplejson.dumps(returned)
    else:
        returned = "[]"
    response('200 OK', [
        ('content-type', 'text/javascript'),
        ('content-length', len(returned)),
    ])
    return returned


@checked
def admin_handle(environ, response):
    _, url, command = environ['PATH_INFO'].split("/")
    log.debug("Admin call: %s %s", url, command)
    cookies = _read_cookies(environ)
    params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
    assert(cookies['sessionid'] in sessions)
    admin = Admin(game_root)
    returned = getattr(admin, command)(**params)
    returned = simplejson.dumps(returned)
    response('200 OK', [
        ('content-type', 'text/javascript'),
        ('content-length', len(returned)),
    ])
    return returned


@checked
def check_player_joined(player_id):
    for instance in instances.values():
        if player_id in instance.players:
            return True
    return False


@checked
def _get_param(environ, param):
    if 'QUERY_STRING' in environ:
        params = dict(urlparse.parse_qsl(environ['QUERY_STRING']))
        if param in params:
            return params[param]
    return None


@checked
def root(environ, response):
    if environ['PATH_INFO'] == '/socket':
        return handle_socket(environ, response)
    elif environ['PATH_INFO'].startswith('/game/'):
        return game_handle(environ, response)
    elif environ['PATH_INFO'].startswith('/control/'):
        return control_handle(environ, response)
    elif environ['PATH_INFO'].startswith('/room/'):
        return room_handle(environ, response)
    elif environ['PATH_INFO'].startswith('/admin/'):
        return admin_handle(environ, response)
    elif environ['PATH_INFO'] == '/':
        if check_player_joined(_get_param(environ, 'player_id')):
            return www_file('/index.html', response)
        else:
            return redirect(master_addr, response)
    else:
        return www_file(environ['PATH_INFO'], response)

@checked
def www_file(path, response):
    filepath = os.path.join(game_root, "assets" + path)
    if os.path.exists(filepath):
        response('200 OK', [('content-type', guess_type(filepath))])
        return [open(filepath).read()]
    else:
        response('404 Not Found', [])
        return "Not Found"

@checked
def redirect(path, response):
    response('301 Moved Permanently', [ ('location', path) ])
    return ""

@checked
def deregister():
    master.deregister_node(host, port)

if __name__ == "__main__":
    try:
        log.info("Starting server")
        parser = OptionParser()

        parser.add_option("-m", "--master", dest="master",
            default="localhost:8081", help="Address of master",
            metavar="KS_MASTER")

        parser.add_option("-a", "--address", dest="address",
            default="localhost:8080", help="Address to serve node on",
            metavar="KS_NODE")

        parser.add_option("-d", "--dbaddr", dest="dbaddr",
            default="localhost:27017", help="Address of mongo server",
            metavar="KS_DBADDR")

        parser.add_option("-g", "--game", dest="game",
            default="/home/ray/projects/rooms/games/demo1",
                help="Path to game dir",
            metavar="KS_GAME")

        (options, args) = parser.parse_args()
        host = options.address.split(":")[0]
        port = int(options.address.split(":")[1])

        dbhost = options.dbaddr.split(":")[0]
        dbport = int(options.dbaddr.split(":")[1])

        init_mongo(dbhost, dbport)

        global master_addr
        master_addr = options.master

        global master
        master = xmlrpclib.ServerProxy('http://%s' % (master_addr,))
        master.register_node(host, port)

        global game_root
        game_root = options.game

        sys.path.append(os.path.join(game_root, "scripts"))

        eventlet.spawn(backdoor.backdoor_server, eventlet.listen(
            ('localhost', 3000)), locals=dict(instances=instances))

        listener = eventlet.listen((host, port))
        wsgi.server(listener, root)
    except:
        log.exception("Exception starting server")
    finally:
        log.info("Server stopped")
        deregister()
