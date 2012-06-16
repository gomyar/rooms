
import time
import random

import eventlet
from eventlet.queue import LightQueue
import simplejson

from actor import Actor
from player_actor import PlayerActor
import container

import logging
log = logging.getLogger("rooms.instance")

class Instance:
    def __init__(self, uid=None, master=None):
        self.uid = uid
        self.player_queues = dict()
        self.players = dict()
        self.area = None
        self.master = master

    def load_map(self, map_id):
        self.area = container.load_area(map_id)

    def sleep(self):
        print "Sleeping instance"

    def call(self, command, player_id, actor_id, kwargs):
        player = self.players[player_id]['player']
        actor = player.room.actors[actor_id]
        if player == actor:
            if command == "exposed_commands":
                return actor.exposed_commands()
            value = actor.command_call(command, **kwargs)
            self.send_to_all("actor_update", **actor.external())
        else:
            if command == "exposed_methods":
                return actor.exposed_methods(player)
            value = actor.interface_call(command, player, **kwargs)
            self.send_to_all("actor_update", **actor.external())
        return value

    def create_instance(self, map_id):
        log.debug("Instance created %s", map_id)

    def send_event(self, player_id, command, **kwargs):
        if player_id in self.player_queues:
            self.player_queues[player_id].put(dict(command=command,
                kwargs=kwargs))

    def send_to_all(self, command, **kwargs):
        for queue in self.player_queues.values():
            queue.put(dict(command=command, kwargs=kwargs))

    def send_to_players(self, player_ids, command, **kwargs):
        for player_id in player_ids:
            self.send_event(player_id, command, **kwargs)

    def send_sync(self, player_id):
        self.player_queues[player_id].put(self.sync(player_id))

    def actors_dict(self):
        return map(lambda a: a.external(), self.area.actors.values())

    def sync(self, player_id):
        player = self.area.actors[player_id]
        return {
            "command": "sync",
            "kwargs" : {
                "actors" : map(lambda a: a.external(),
                    player.room.actors.values()),
                "now" : time.time(),
                "map" : "map1.json",
                "player_log" : player.log,
            }
        }

    def connect(self, player_id):
        log.debug("Connecting %s", player_id)
        self.players[player_id]['connected'] = True
        if player_id in self.player_queues:
            log.debug("Disconnecting existing player %s", player_id)
            self.disconnect(player_id)
        queue = LightQueue()
        self.player_queues[player_id] = queue
        return queue

    def disconnect(self, player_id):
        log.debug("Disconnecting %s", player_id)
        queue = self.player_queues.pop(player_id)
        queue.put(dict(command='disconnect'))

    def disconnect_queue(self, queue):
        for player_id, q in self.player_queues.items():
            if q == queue:
                self.player_queues.pop(player_id)

    def register(self, player_id):
        self.players[player_id] = dict(connected=False)

        actor = PlayerActor(player_id)
        self.players[player_id]['player'] = actor
        self.area.actors[player_id] = actor
        actor.instance = self
        self.area.player_joined_instance(actor, self.area.entry_point_room_id)
        self.send_to_all("player_joined_instance", **actor.external())

        log.info("Player joined instance: %s", player_id)

    def deregister(self, player_id):
        self.disconnect(player_id)
        actor = self.area.actors.pop(player_id)
        self.area.actor_left_instance(actor)
        self.send_to_all("actor_left_instance", actor_id=player_id)
        self.players.pop(player_id)
        self.master.player_left(player_id, self.uid)

        log.info("Player left instance: %s", player_id)

    def kickoff(self):
        self.area.kickoff_npcs(self)
