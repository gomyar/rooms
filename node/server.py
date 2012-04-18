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

from instance import Instance

from eventlet.queue import LightQueue
from eventlet.queue import Empty

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

instances = dict()
sessions = dict()

master = None

def _read_cookies(environ):
    cookie_str = environ['HTTP_COOKIE']
    cookies = cookie_str.split(';')
    cookies = map(lambda c: c.strip().split('='), cookies)
    return dict(cookies)

@websocket.WebSocketWSGI
def handle_socket(ws):
    player_id = None
    queue = LightQueue()
    instance = None
    try:
        cookies = _read_cookies(ws.environ)
        player_id = ws.wait()
        instance_uid = ws.wait()
        instance = instances[instance_uid]
        log.debug("registering %s at %s", player_id, instance_uid)
        instance.register(player_id, queue)
        sessions[cookies['sessionid']] = player_id
        ws.send(simplejson.dumps([instance.sync(player_id)]))
        while not ws.websocket_closed:
            try:
                command = queue.get(timeout=5)
                commands = [ command ]
                while queue.qsize() > 0:
                    commands.append(queue.get())
                dumps = simplejson.dumps(commands)
                ws.send(dumps)
            except Empty, err:
                ws.send(simplejson.dumps([{'command':"heartbeat"}]))
    except:
        log.exception("Exception from websocket")
    finally:
        if instance:
            if instance.deregister(player_id, queue):
                log.debug("Calling player left")
                master.player_left(player_id, instance_uid)


@websocket.WebSocketWSGI
def handle_gamesocket(ws):
    player_id = None
    queue = LightQueue()
    instance = None
    player_id = ws.wait()
    instance_uid = ws.wait()
    instance = instances[instance_uid]
    while not ws.websocket_closed:
        command_dict = simplejson.loads(ws.wait())
        command = command_dict['command']
        kwargs = command_dict['kwargs']
        log.debug("Calling %s(%s)", command, kwargs)
        instance.call(command, kwargs)


def game_handle(environ, response):
    _, url, instance_uid, actor_id, command = environ['PATH_INFO'].split("/")
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


def control_handle(environ, response):
    path = environ['PATH_INFO'].replace("/control/", "")
    params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))

    returned = ""

    if path == "player_joins":
        instance_uid = params['instance_uid']
        player_id = params['player_id']
        instance = instances[instance_uid]
        instance.player_joins(player_id)
        returned = '{"success":true}'
        log.info("Player %s joined instance %s", player_id, instance_uid)

    if path == "create_instance":
        map_id = params['map_id']
        uid = str(uuid.uuid1())
        instance = Instance()
        instance.load_map(map_id)
        instances[uid] = instance
        returned = '{"instance_uid": "%s"}' % (uid,)
        log.info("Instance created %s : %s", map_id, uid)

    response('200 OK', [
        ('content-type', 'text/javascript'),
        ('content-length', len(returned)),
    ])
    return returned


def check_player_joined(player_id):
    for instance in instances.values():
        if player_id in instance.players:
            return True
    return False


def _get_param(environ, param):
    if 'QUERY_STRING' in environ:
        params = dict(urlparse.parse_qsl(environ['QUERY_STRING']))
        if param in params:
            return params[param]
    return None


def root(environ, response):
    if environ['PATH_INFO'] == '/socket':
        return handle_socket(environ, response)
    elif environ['PATH_INFO'].startswith('/game/'):
        return game_handle(environ, response)
    elif environ['PATH_INFO'].startswith('/control/'):
        return control_handle(environ, response)
    elif environ['PATH_INFO'] == '/':
        if check_player_joined(_get_param(environ, 'player_id')):
            return www_file('/index.html', response)
        else:
            return redirect("http://:9001", response)
    else:
        return www_file(environ['PATH_INFO'], response)

def www_file(path, response):
    filepath = os.path.join(os.path.dirname(__file__), "www" + path)
    if os.path.exists(filepath):
        response('200 OK', [('content-type', guess_type(filepath))])
        return [open(filepath).read()]
    else:
        response('404 Not Found', [])
        return "Not Found"

def redirect(path, response):
    response('301 Moved Permanently', [ ('location', path) ])
    return ""

if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("-m", "--master", dest="master",
        default="localhost:8081", help="Address of master",
        metavar="KS_MASTER")

    parser.add_option("-a", "--address", dest="address",
        default="localhost:8080", help="Address to serve node on",
        metavar="KS_NODE")

    (options, args) = parser.parse_args()
    host = options.address.split(":")[0]
    port = int(options.address.split(":")[1])

    master_addr = options.master

    global master
    master = xmlrpclib.ServerProxy('http://%s' % (master_addr,))
    master.register_node(host, port)

    eventlet.spawn(backdoor.backdoor_server, eventlet.listen(
        ('localhost', 3000)), locals=dict(instances=instances))

    listener = eventlet.listen((host, port))
    wsgi.server(listener, root)
