
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
from utils import _read_cookies
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
        cookies = _read_cookies(environ)
        player_id = None
        queue = None
        try:
            token = ws.receive()
            admin_name = self.node.admin_by_token(token)
            player_actor = self.node.player_by_token(token)
            if admin_name:
                player_id = admin_name
                queue = self.admin_connect(player_id)
            elif player_actor:
                player_id = player_actor.player.username
                queue = self.connect(player_id)
            else:
                log.debug("No such player for token")
                return

            log.debug("Connected to queue")
            self.sessions[cookies['sessionid']] = player_id
            log.debug("Sending sync")
            if admin_name:
                self.admin_sync(admin_name)
            else:
                self.send_sync(player_id)
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
        cookies = _read_cookies(environ)
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        returned = self.node.call(self.sessions[cookies['sessionid']], command,
            dict(params))
        return _json_return(response, returned)


    @checked
    def actors_handle(self, environ, response):
        _, url, actor_id, command = \
            environ['PATH_INFO'].split("/")
        log.debug("Actor request call %s, %s", url, command)
        cookies = _read_cookies(environ)
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        returned = self.node.actor_request(self.sessions[cookies['sessionid']],
            actor_id, command, dict(params))
        return _json_return(response, returned)


    @checked
    def room_handle(self, environ, response):
        _, url, area_map = environ['PATH_INFO'].split("/")
        cookies = _read_cookies(environ)
        player_actor = self.node.players[self.sessions[cookies['sessionid']]]\
            ['player']
        return _json_return(response, player_actor.room.external())


    @checked
    def admin_handle(self, environ, response):
        _, url, command = environ['PATH_INFO'].split("/")
        log.debug("Admin call: %s %s", url, command)
        cookies = _read_cookies(environ)
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        assert(cookies['sessionid'] in self.sessions)
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

    def send_update(self, player_id, command, **kwargs):
        if player_id in self.player_queues:
            self.player_queues[player_id].put(dict(command=command,
                kwargs=kwargs))

    def send_to_players(self, player_ids, command, **kwargs):
        for player_id in player_ids:
            self.send_update(player_id, command, **kwargs)

    def send_to_admins(self, command, **kwargs):
        for admin_name in self.node.admins:
            self.admin_queues[admin_name].put(dict(command=command,
                kwargs=kwargs))

    def send_sync(self, player_id):
        self.player_queues[player_id].put(self._sync(player_id))

    def _sync(self, player_id):
        player = self.node.players[player_id]['player']
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

    def admin_sync(self, admin_name):
        self.admin_queues[admin_name].put(self._admin_sync(admin_name))

    def _admin_sync(self, admin_name):
        admin = self.node.admins[admin_name]
        room = self.node.areas[admin['area_id']].rooms[admin['room_id']]
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

    def connect(self, player_id):
        log.debug("Connecting %s", player_id)
        self.node.players[player_id]['connected'] = True
        if player_id in self.player_queues:
            log.debug("Disconnecting existing player %s", player_id)
            self.disconnect(player_id)
        queue = gevent.queue.Queue()
        self.player_queues[player_id] = queue
        return queue

    def admin_connect(self, admin_name):
        log.debug("Connecting %s", admin_name)
        self.node.admins[admin_name]['connected'] = True
        queue = gevent.queue.Queue()
        self.admin_queues[admin_name] = queue
        return queue

    def disconnect(self, player_id):
        log.debug("Disconnecting %s", player_id)
        queue = self.player_queues.pop(player_id)
        queue.put(dict(command='disconnect'))

    def disconnect_queue(self, queue):
        for player_id, q in self.player_queues.items():
            if q == queue:
                self.player_queues.pop(player_id)
        # disconnect admin

