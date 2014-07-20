
import time
import gevent

import json
from rooms.rpc import WSGIRPCClient
from ws4py.client.geventclient import WebSocketClient

import logging
logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("rooms.client")


class Actor(object):
    def __init__(self, conn, data):
        self.update(data)
        self._conn = conn

    def update(self, data):
        self.__dict__.update(data)

    def __repr__(self):
        return "<%s %s>" % (self.actor_type, self.name,)

    def position(self):
        return (0, 0)

    def x(self):
        now = self._conn.get_now()
        path = list(self.path)
        start = path[0]
        while path and now > path[0][2]:
            start = path.pop(0)
        if not path:
            return self.path[-1][0]
        start_x, start_y, start_time = start
        end_x, end_y, end_time = path[0]

        if now > end_time:
            return end_x
        diff_x = end_x - start_x
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_x
        inc = (now - start_time) / diff_t
        return start_x + diff_x * inc

    def y(self):
        now = self._conn.get_now()
        path = list(self.path)
        start = path[0]
        while path and now > path[0][2]:
            start = path.pop(0)
        if not path:
            return self.path[-1][1]
        start_x, start_y, start_time = start
        end_x, end_y, end_time = path[0]

        if now > end_time:
            return end_y
        diff_y = end_y - start_y
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_y
        inc = (now - start_time) / diff_t
        return start_y + diff_y * inc

    def position(self):
        return (self.x(), self.y())


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

    def get_now(self):
        local_now = time.time()
        ticks = local_now - self.local_time
        return ticks + self.server_time

    def create_game(self, owner_username, **options):
        return self.master.create_game(owner_username=owner_username,
            **options)

    def end_game(self, owner_username, game_id):
        raise NotImplemented("")

    def list_games(self, owner_username):
        raise NotImplemented("")

    def player_info(self, username):
        return self.master.player_info(username=username)

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
                    messages = json.loads(str(sock_msg))
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

    def admin_connect(self, username, area_id, room_id):
        node = self.master.admin_connects(username=username, area_id=area_id,
            room_id=room_id)
        self._connect_to_node(**node)

    def _command_sync(self, data):
        log.debug("Sync: %s", data)
        self.set_now(data['now'])

        self.player_actor = Actor(self, data['player_actor'])

        self.actors = {}
        for actor in data['actors']:
            self.actors[actor['actor_id']] = Actor(self, actor)

    def _command_heartbeat(self, data):
        log.debug("Heartbeat")

    def _command_actor_update(self, data):
        if data['actor_id'] == self.player_actor.actor_id:
            self.player_actor.update(data)
        elif data.get('docked_with') == self.player_actor.actor_id:
            self.player_actor['docked_actors'][data['actor_type']]\
                [data['actor_id']] = data
        else:
            if data['actor_id'] not in self.actors:
                self.actors[data['actor_id']] = Actor(self, data)
            else:
                self.actors[data['actor_id']].update(data)

        log.debug("Actor updated: %s", data)

    def _command_remove_actor(self, data):
        log.debug("actor removed; %s", data)
        if data['actor_id'] in self.actors:
            self.actors.pop(data['actor_id'])

    def _command_moved_node(self, data):
        log.debug("moving node: %s", data)
        raise Exception("Not implemented")

