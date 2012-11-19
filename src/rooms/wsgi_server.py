
import os
import uuid

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from gevent.queue import Empty

import urlparse
from mimetypes import guess_type

import simplejson

from rooms.instance import Instance
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


class WSGIServer(object):
    def __init__(self, host, port, node):
        self.host = host
        self.port = port
        self.node = node
        self.rpc_objects = {
            'game': self.game_handle,
            'room': self.room_handle,
            'admin': self.admin_handle,
        }

    def serve_forever(self):
        server = pywsgi.WSGIServer((self.host, self.port), self.handle,
            handler_class=WebSocketHandler)
        server.serve_forever()

    def _check_player_joined(self, player_id):
        for instance in self.node.instances.values():
            if player_id in instance.players:
                return True
        return False

    def handle(self, environ, response):
        rest_object = environ['PATH_INFO'].strip('/').split('/')[0]
        if environ['PATH_INFO'] == '/socket':
            return self.handle_socket(environ, response)
        elif rest_object in self.rpc_objects:
            return self.rpc_objects[rest_object](environ, response)
        elif environ['PATH_INFO'] == '/':
            if self._check_player_joined(_get_param(environ, 'player_id')):
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
        instance = None
        queue = None
        try:
            player_id = ws.receive()
            instance_uid = ws.receive()
            instance = self.node.instances[instance_uid]
            log.debug("registering %s at %s", player_id, instance_uid)
            queue = instance.connect(player_id)
            log.debug("Connected to queue")
            self.node.sessions[cookies['sessionid']] = player_id
            log.debug("Sending sync")
            instance.send_sync(player_id)
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
            if instance and queue:
                instance.disconnect_queue(queue)


    @checked
    def game_handle(self, environ, response):
        _, url, instance_uid, actor_id, command = \
            environ['PATH_INFO'].split("/")
        log.debug("Game call %s, %s, %s, %s", url, instance_uid, actor_id,
            command)
        cookies = _read_cookies(environ)
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        instance = self.node.instances[instance_uid]
        returned = instance.call(command, self.node.sessions[cookies['sessionid']],
            actor_id, dict(params))
        return _json_return(response, returned)


    @checked
    def room_handle(self, environ, response):
        _, url, instance_uid = environ['PATH_INFO'].split("/")
        log.debug("Room call: %s %s", url, instance_uid)
        cookies = _read_cookies(environ)
        instance = self.node.instances[instance_uid]
        returned = instance.players[self.node.sessions[cookies['sessionid']]]\
            ['player'].room.external()
        return _json_return(response, returned)


    @checked
    def admin_handle(self, environ, response):
        _, url, command = environ['PATH_INFO'].split("/")
        log.debug("Admin call: %s %s", url, command)
        cookies = _read_cookies(environ)
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        assert(cookies['sessionid'] in self.node.sessions)
        admin = Admin(self.node.game_root)
        returned = getattr(admin, command)(**params)
        return _json_return(response, returned)


    @checked
    def www_file(self, path, response):
        filepath = os.path.join(self.node.game_root, "assets" + path)
        if os.path.exists(filepath):
            response('200 OK', [('content-type', guess_type(filepath))])
            return [open(filepath).read()]
        else:
            response('404 Not Found', [])
            return "Not Found"

    @checked
    def redirect(self, path, response):
        response('301 Moved Permanently', [ ('location', path) ])
        return ""
