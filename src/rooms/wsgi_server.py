
import os
import uuid
import time

import gevent
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from gevent.queue import Empty

import urlparse
from mimetypes import guess_type

import simplejson

import rooms
from rooms.area import Area
from rooms.admin import Admin

from utils import checked
from utils import _get_param

import logging
log = logging.getLogger("rooms.wsgi")


def _json_return(response, returned):
    if returned:
        returned = simplejson.dumps(returned)
    else:
        returned = "[]"
    response('200 OK', [
        ('content-type', 'text/javascript'),
        ('content-length', len(returned)),
    ])
    return returned


def _rooms_filepath(filepath):
    return os.path.join(os.path.dirname(os.path.abspath(rooms.__file__)),
        "assets", filepath.lstrip('/'))


class WSGIServer(object):
    def __init__(self, host, port, node):
        self.host = host
        self.port = port
        self.node = node
        self.rpc_objects = {
            'game': self.game_handle,
            'actors': self.actors_handle,
            'room': self.room_handle,
            'admin': self.admin_handle,
        }
        self.sessions = dict()
        self.player_queues = dict()
        self.admin_queues = dict()

    def serve_forever(self):
        server = pywsgi.WSGIServer((self.host, self.port), self.handle,
            handler_class=WebSocketHandler)
        server.serve_forever()

    def _check_player_joined(self, token):
        return self.node.player_by_token(token)

    def handle(self, environ, response):
        rest_object = environ['PATH_INFO'].strip('/').split('/')[0]
        if environ['PATH_INFO'] == '/socket':
            return self.handle_socket(environ, response)
        elif rest_object in self.rpc_objects:
            return self.rpc_objects[rest_object](environ, response)
        elif environ['PATH_INFO'] == '/':
            if self._check_player_joined(_get_param(environ, 'token')):
                return self.www_file('/index.html', response)
            else:
                return self.www_file('/player_error.html', response)
        else:
            return self.www_file(environ['PATH_INFO'], response)

    @checked
    def handle_socket(self, environ, response):
        ws = environ["wsgi.websocket"]
        player_id = None
        queue = None
        try:
            token = ws.receive()
            game_id, admin_name = self.node.admin_by_token(token)
            player_actor = self.node.player_by_token(token)
            if admin_name:
                player_id = admin_name
                queue = self.admin_connect(game_id, admin_name)
            elif player_actor:
                player_id = player_actor.player.username
                game_id = player_actor.player.game_id
                queue = self.connect(game_id, player_id)
            else:
                log.debug("No such player for token: %s", token)
                return

            log.debug("Connected to queue")
            self.sessions[token] = game_id, player_id
            log.debug("Sending sync")
            if admin_name:
                self.admin_sync(game_id, admin_name)
            else:
                self.send_sync(game_id, player_id)
            log.debug("Sync sent")
            connected = True
            while connected:
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
            if queue:
                self.disconnect_queue(queue)

    @checked
    def game_handle(self, environ, response):
        _, url, command = \
            environ['PATH_INFO'].split("/")
        log.debug("Game call %s, %s", url, command)
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        token = params.pop('token')
        game_id, player_id = self.sessions[token]
        returned = self.node.call(game_id, player_id, command, params)
        return _json_return(response, returned)


    @checked
    def actors_handle(self, environ, response):
        _, url, actor_id, command = \
            environ['PATH_INFO'].split("/")
        log.debug("Actor request call %s, %s", url, command)
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        token = params.pop('token')
        game_id, player_id = self.sessions[token]
        returned = self.node.actor_request(game_id, player_id,
            actor_id, command, params)
        return _json_return(response, returned)


    @checked
    def room_handle(self, environ, response):
        _, url, area_map = environ['PATH_INFO'].split("/")
        # Expecting GET
        params = dict(urlparse.parse_qsl(environ['QUERY_STRING']))
        token = params.pop('token')
        game_id, player_id = self.sessions[token]
        if player_id in self.node.admins and token == \
            self.node.admins[player_id]['token']:
            admin_info = self.node.admins[player_id]
            room = self.node.areas[admin_info['game_id'], admin_info['area_id']].rooms[
                admin_info['room_id']]
            return _json_return(response, room.external())
        else:
            player_actor = self.node.players[self.sessions[token]]['player']
            return _json_return(response, player_actor.room.external())


    @checked
    def admin_handle(self, environ, response):
        _, url, command = environ['PATH_INFO'].split("/")
        log.debug("Admin call: %s %s", url, command)
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        token = params.pop('token')
        assert(token in self.sessions)
        admin = Admin(self.node.game_root)
        returned = getattr(admin, command)(**params)
        return _json_return(response, returned)


    @checked
    def www_file(self, path, response):
        filepath = os.path.join(self.node.game_root, "assets" + path)
        if os.path.exists(filepath):
            response('200 OK', [('content-type', guess_type(filepath))])
            return [open(filepath).read()]
        elif os.path.exists(_rooms_filepath(path)):
            response('200 OK', [('content-type', guess_type(_rooms_filepath(
                path)))])
            return [open(_rooms_filepath(path)).read()]
        else:
            response('404 Not Found', [])
            return "File Not Found: %s" % (path,)

    @checked
    def redirect(self, path, response):
        response('301 Moved Permanently', [ ('location', path) ])
        return ""

    def send_update(self, game_id, player_id, command, **kwargs):
        if (game_id, player_id) in self.player_queues:
            self.player_queues[game_id, player_id].put(dict(command=command,
                kwargs=kwargs))

    def send_to_admins(self, area, command, **kwargs):
        log.debug("Sending admin command: %s area:%s game:%s", command, area.area_id, area.game_id)
        for game_id, username in self.node.admins:
            if (game_id, username) in self.admin_queues and \
                    game_id == area.game_id:
                log.debug("Sending admin command %s to %s:%s", command, game_id, username)
                self.admin_queues[game_id, username].put(dict(command=command,
                    kwargs=kwargs))

    def send_sync(self, game_id, player_id):
        self.player_queues[game_id, player_id].put(self._sync(game_id, player_id))

    def _sync(self, game_id, player_id):
        player = self.node.players[game_id, player_id]['player']
        return {
            "command": "sync",
            "kwargs" : {
                "player_actor" : player.internal(),
                "actors" : map(lambda a: a.external(),
                    player.visible_actors()),
                "now" : time.time(),
                "map" : "map1.json",
                "player_log" : player.log,
            }
        }

    def admin_sync(self, game_id, admin_name):
        self.admin_queues[game_id, admin_name].put(
            self._admin_sync(game_id, admin_name))

    def _admin_sync(self, game_id, admin_name):
        admin = self.node.admins[game_id, admin_name]
        room = self.node.areas[game_id, admin['area_id']].rooms[admin['room_id']]
        return {
            "command": "sync",
            "kwargs" : {
                "actors" : map(lambda a: a.internal(),
                    room.actors.values()),
                "now" : time.time(),
                "map" : "map1.json",
                "player_log" : [],
            }
        }

    def connect(self, game_id, player_id):
        log.debug("Connecting %s", player_id)
        self.node.players[game_id, player_id]['connected'] = True
        if player_id in self.player_queues:
            log.debug("Disconnecting existing player %s", player_id)
            self.disconnect(game_id, player_id)
        queue = gevent.queue.Queue()
        self.player_queues[game_id, player_id] = queue
        return queue

    def admin_connect(self, game_id, admin_name):
        log.debug("Connecting %s: %s", game_id, admin_name)
        self.node.admins[game_id, admin_name]['connected'] = True
        queue = gevent.queue.Queue()
        self.admin_queues[game_id, admin_name] = queue
        return queue

    def disconnect(self, game_id, player_id):
        log.debug("Disconnecting %s %s", game_id, player_id)
        queue = self.player_queues.pop((game_id, player_id))
        queue.put(dict(command='disconnect'))

    def disconnect_queue(self, queue):
        for (game_id, player_id), q in self.player_queues.items():
            if q == queue:
                self.player_queues.pop(game_id, player_id)
        # disconnect admin

    def disconnect_game(self, game_id):
        for (g_id, player_id), q in self.player_queues.items():
            if g_id == game_id:
                self.disconnect(g_id, player_id)
