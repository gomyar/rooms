
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

import logging
import logging.config
logging.config.fileConfig("logging.conf")
log = logging.getLogger("rooms.wsgi")


def checked(func):
    def tryexcept(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            log.exception("Exception calling %s", func)
            raise
    return tryexcept

def _read_cookies(environ):
    cookie_str = environ['HTTP_COOKIE']
    cookies = cookie_str.split(';')
    cookies = map(lambda c: c.strip().split('='), cookies)
    return dict(cookies)


@checked
def _get_param(environ, param):
    if 'QUERY_STRING' in environ:
        params = dict(urlparse.parse_qsl(environ['QUERY_STRING']))
        if param in params:
            return params[param]
    return None


class WSGIServer(object):
    def __init__(self, node):
        self.node = node

    def serve_forever(self):
        server = pywsgi.WSGIServer(("", 8080), self.handle,
            handler_class=WebSocketHandler)
        server.serve_forever()

    def handle(self, environ, response):
        if environ['PATH_INFO'] == '/socket':
            cookies = _read_cookies(environ)
            return self.handle_socket(environ["wsgi.websocket"], cookies)
        elif environ['PATH_INFO'].startswith('/game/'):
            return self.game_handle(environ, response)
        elif environ['PATH_INFO'].startswith('/control/'):
            return self.control_handle(environ, response)
        elif environ['PATH_INFO'].startswith('/room/'):
            return self.room_handle(environ, response)
        elif environ['PATH_INFO'].startswith('/admin/'):
            return self.admin_handle(environ, response)
        elif environ['PATH_INFO'].startswith('/controller/'):
            return self.handle_controller(environ, response)
        elif environ['PATH_INFO'] == '/':
            if self.check_player_joined(_get_param(environ, 'player_id')):
                return self.www_file('/index.html', response)
            else:
                return self.redirect(master_addr, response)
        else:
            return self.www_file(environ['PATH_INFO'], response)

    def handle_controller(self, environ, response):
        if not self.node.controller:
            raise Exception("This is not a Controller node")
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        controller_call = environ['PATH_INFO'].replace('/controller/', '')
        controller_method = getattr(self.node.controller, controller_call)
        returned = controller_method(**params)
        if returned :
            returned = simplejson.dumps(returned)
        else:
            returned = "[]"
        response('200 OK', [
            ('content-type', 'text/javascript'),
            ('content-length', len(returned)),
        ])
        return returned


    @checked
    def handle_socket(self, ws, cookies):
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
    def control_handle(self, environ, response):
        path = environ['PATH_INFO'].replace("/control/", "")
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))

        returned = ""

        if path == "player_joins":
            instance_uid = params['instance_uid']
            player_id = params['player_id']
            self.node.player_joins(instance_uid, player_id)
            returned = '{"success":true}'
            log.info("Player %s joined instance %s", player_id, instance_uid)

        if path == "create_instance":
            map_id = params['map_id']
            uid = self.node.create_instance(map_id)
            returned = '{"instance_uid": "%s"}' % (uid,)
            log.info("Instance created %s : %s", map_id, uid)

        response('200 OK', [
            ('content-type', 'text/javascript'),
            ('content-length', len(returned)),
        ])
        return returned


    @checked
    def room_handle(self, environ, response):
        _, url, instance_uid = environ['PATH_INFO'].split("/")
        log.debug("Room call: %s %s", url, instance_uid)
        cookies = _read_cookies(environ)
        instance = self.node.instances[instance_uid]
        returned = instance.players[sessions[cookies['sessionid']]]\
            ['player'].room.external()
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
    def admin_handle(self, environ, response):
        _, url, command = environ['PATH_INFO'].split("/")
        log.debug("Admin call: %s %s", url, command)
        cookies = _read_cookies(environ)
        params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))
        assert(cookies['sessionid'] in self.node.sessions)
        admin = Admin(self.node.game_root)
        returned = getattr(admin, command)(**params)
        returned = simplejson.dumps(returned)
        response('200 OK', [
            ('content-type', 'text/javascript'),
            ('content-length', len(returned)),
        ])
        return returned


    @checked
    def check_player_joined(self, player_id):
        for instance in self.node.instances.values():
            if player_id in instance.players:
                return True
        return False


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
