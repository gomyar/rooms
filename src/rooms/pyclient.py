
import time
import gevent

import simplejson
from rooms.wsgi_rpc import WSGIRPCClient
from ws4py.client.geventclient import WebSocketClient

import logging
logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("rooms.client")


class Actor(object):
    def __init__(self, data):
        self.__dict__.update(data)

    def __repr__(self):
        return "<%s %s>" % (self.actor_type, self.name,)


class RoomsConnection(object):
    def __init__(self, master_host='localhost', master_port=8082):
        self.master_host = master_host
        self.master_port = master_port
        self.master = WSGIRPCClient(master_host, master_port)
        self.ws = None
        self.connected = False
        self.gthread = None

        # Game data
        self.server_time = None
        self.local_time = None
        self.node = None
        self.token = None

        self.room = dict(width=500, height=500, position=[0, 0], map_objects=[], visibility_grid=dict(width =0, height =0, gridsize=10))

        self.actors = {}
        self.player_actor = None

        self._commands = {
            "sync": self._command_sync,
            "actor_update": self._command_actor_update,
            "remove_actor": self._command_remove_actor,
            "moved_node": self._command_moved_node,
            "heartbeat": self._command_heartbeat,
        }

    def create_game(self, owner_id, **options):
        pass

    def player_info(self, username, game_id):
        return self.master.player_info(username=username, game_id=game_id)

    def join_game(self, username, game_id, area_id, room_id, **state):
        node = self.master.join_game(username=username, game_id=game_id,
            start_area_id=area_id, start_room_id=room_id, **state)
        self._connect_to_node(**node)

    def connect_to_game(self, username, game_id):
        node = self.master.connect_to_game(username=username, game_id=game_id)
        self._connect_to_node(**node)

    def _connect_to_node(self, host, port, token):
        log.debug("Connecting to node ws://%s:%s/ with token %s", host, port,
            token)
        self.ws = WebSocketClient("ws://%s:%s/socket" % (host, port),
            protocols=['http-only', 'chat'])
        self.ws.connect()

        self.ws.send(token)

        self.node = WSGIRPCClient(host, port, namespace="game")
        self.token = token
        self._start_listen_thread()
        self.connected = True

    def _start_listen_thread(self):
        self.gthread = gevent.spawn(self.listen_to_events)

    def listen_to_events(self):
        while self.connected:
            try:
                sock_msg = self.ws.receive()
                log.debug("Received :%s", sock_msg)
                if sock_msg:
                    messages = simplejson.loads(str(sock_msg))
                    for message in messages:
                        self._commands[message['command']](
                            message.get('kwargs'))
                else:
                    self.connected = False
            except:
                log.exception("disconnected")
                self.connected = False
                self.ws = None
                return

    def call(self, method, **kwargs):
        kwargs['token'] = self.token
        return getattr(self.node, method)(**kwargs)

    def set_now(self, now):
        self.server_time = now
        self.local_time = time.time()

    def _command_sync(self, data):
        log.debug("Sync: %s", data)
        self.set_now(data['now'])

        self.player_actor = Actor(data['player_actor'])

        self.actors = {}
        for actor in data['actors']:
            self.actors[actor['actor_id']] = Actor(actor)

    def _command_heartbeat(self, data):
        log.debug("Heartbeat")

    def _command_actor_update(self, data):
        log.debug("Actor updated: %s", data)

    def _command_remove_actor(self, data):
        log.debug("actor removed; %s", data)

    def _command_moved_node(self, data):
        log.debug("moving node: %s", data)

