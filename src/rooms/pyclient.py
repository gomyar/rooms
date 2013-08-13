
import time
import threading

from rooms.wsgi_rpc import WSGIRPCClient
from websocket import create_connection

import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("rooms.client")


class Actor(object):
    def __init__(self, data):
        self.__dict__.update(data)


class RoomsConnection(object):
    def __init__(self, master_host='localhost', master_port=8082):
        self.master_host = master_host
        self.master_port = master_port
        self.master = WSGIRPCClient(master_host, master_port)
        self.node_socket = None

        # Game data
        self.server_time = None
        self.local_time = None
        self.token = None

        self.room = dict(width=500, height=500, position=[0, 0], map_objects=[], visibility_grid=dict(width =0, height =0, gridsize=10))

        self.actors = {}
        self.player_actor = None

        self._commands = {
            "sync": self._command_sync,
            "actor_update": self._command_actor_update,
            "remove_actor": self._command_remove_actor,
            "moved_node": self._command_moved_node,
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
        self.node_socket = create_connection("ws://%s:%s/socket" % (host, port),
            header=['HTTP_COOKIE: sessionid=pyclient'])
        self.node_socket.send(token)

        self._start_listen_thread()

    def _start_listen_thread(self):
        self._thread = threading.Thread(target=self.listen_to_events)
        self._thread.daemon = True
        self._thread.start()

    def listen_to_events(self):
        while self.node_socket.connected:
            try:
                sock_msg = self.node_socket.recv()
                log.debug("Received :%s", sock_msg)
                messages = simplejson.loads(sock_msg)
                for message in messages:
                    self.callbacks[message['command']](**message['kwargs'])
            except:
                log.exception("disconnected")
                return

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

    def _command_actor_update(self, data):
        log.debug("Actor updated: %s", data)

    def _command_remove_actor(self, data):
        log.debug("actor removed; %s", data)

    def _command_moved_node(self, data):
        log.debug("moving node: %s", data)

