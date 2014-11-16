
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
        self._data = dict()
        self._data.update(data)
        self._conn = conn

    def update(self, data):
        self.__dict__.update(data)

    def __repr__(self):
        return "<%s %s>" % (self.actor_type, self.name,)

    def __getattr__(self, name):
        return self._data.get(name)

    def __getitem__(self, name):
        return self._data(name)

    def _calc_d(self, start_d, end_d):
        now = self._conn.get_now()
        start_time = self.vector['start_time']
        end_time = self.vector['end_time']
        if now > end_time:
            return end_d
        diff_x = end_d - start_d
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_d
        inc = (now - start_time) / diff_t
        return start_d + diff_x * inc

    def x(self):
        return self._calc_d(self.vector['start_pos']['x'],
            self.vector['end_pos']['x'])

    def y(self):
        return self._calc_d(self.vector['start_pos']['y'],
            self.vector['end_pos']['y'])

    def z(self):
        return self._calc_d(self.vector['start_pos']['z'],
            self.vector['end_pos']['z'])

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
        self.game_id = None
        self.token = None

        self.room = { 'topleft': {'x': 0, 'y': 0, 'z': 0},
            'bottomright': {'x': 0, 'y': 0, 'z': 0}, 'map_objects': [] }
        self.actors = {}
        self.player_actor = None

        self._commands = {
            "sync": self._command_sync,
            "actor_update": self._command_actor_update,
            "remove_actor": self._command_remove_actor,
            "moved_node": self._command_moved_node,
            "bounce_to_master": self._command_bounce_to_master,
        }

    def get_now(self):
        local_now = time.time()
        ticks = local_now - self.local_time
        return ticks + self.server_time

    def create_game(self, owner_id, **options):
        return self.master.call("master_game/create_game", owner_id=owner_id,
            **options)

    def end_game(self, owner_username, game_id):
        raise NotImplemented("")

    def list_games(self, owner_username):
        raise NotImplemented("")

    def all_players_for(self, username):
        return self.master.call("master_game/all_players_for",
            username=username)

    def join_game(self, username, game_id, area_id, room_id, **state):
        node = self.master.call("master_game/join_game", username=username,
            game_id=game_id, **state)
        self._connect_to_node(node['node'][0], node['node'][1], game_id,
            node['token'])

    def connect_to_game(self, username, game_id):
        node = self.master.call("master_game/player_connects",
            username=username, game_id=game_id)
        self._connect_to_node(node['node'][0], node['node'][1], game_id,
            node['token'])

    def _connect_to_node(self, host, port, game_id, token):
        log.debug("Connecting to node ws://%s:%s/ with token %s", host, port,
            token)
        self.ws = WebSocketClient("ws://%s:%s/node_game/player_connects/%s/%s" \
            % (host, port, game_id, token), protocols=['http-only', 'chat'])
        self.ws.connect()

        self.node = WSGIRPCClient(host, port)
        self.token = token
        self.game_id = game_id
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
                    message = json.loads(str(sock_msg))
                    self._commands[message['command']](message['data'])
                else:
                    self.connected = False
            except:
                log.exception("disconnected")
                self.connected = False
                self.ws = None
                return

    def call_command(self, method, **kwargs):
        return self.node.call("node_game/actor_call/%s/%s/%s" % (
            self.game_id, self.token, method), **kwargs)

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

    def _command_bounce_to_master(self, data):
        log.debug("Bounce to master")
        raise Exception("Not implemented")
