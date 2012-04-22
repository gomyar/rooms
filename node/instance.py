
import time
import random

import eventlet
import simplejson

from actor import Actor
from player_actor import PlayerActor
import container

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

class Instance:
    def __init__(self):
        self.queues = set()
        self.player_queues = dict()
        self.players = dict()
        self.area = None

    def load_map(self, map_id):
        self.area = container.load_area(map_id)

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

    def player_joins(self, player_id):
        self.players[player_id] = dict(connected=False)
        log.debug("Player joined: %s", player_id)

    def create_instance(self, map_id):
        log.debug("Instance created %s", map_id)

    def register_actor(self, player_id, room_id='lobby'):
        if player_id in self.area.actors:
            self.deregister_actor(player_id)

        actor = PlayerActor(player_id)
        self.players[player_id]['player'] = actor
        self.players[player_id]['connected'] = True
        self.area.actors[player_id] = actor
        actor.instance = self
        self.area.actor_enters(actor, self.area.entry_point_room_id,
            self.area.entry_point_door_id)
        self.send_to_all("actor_joined", **actor.external())

    def deregister_actor(self, player_id):
        if player_id in self.area.actors:
            actor = self.area.actors.pop(player_id)
            self.area.actor_exits(actor)
            self.send_to_all("actor_left", player_id=player_id)

    def send_event(self, player_id, event_id, kwargs):
        for queue in self.player_queues[player_id]:
            queue.put(dict(command=event_id, kwargs=kwargs))

    def send_to_all(self, command, **kwargs):
        for queue in self.queues:
            queue.put(dict(command=command, kwargs=kwargs))

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

    def register(self, player_id, queue):
        self.queues.add(queue)
        if player_id not in self.player_queues:
            self.register_actor(player_id)
            self.player_queues[player_id] = []
        self.player_queues[player_id].append(queue)

    def deregister(self, player_id, queue):
        self.queues.remove(queue)
        self.player_queues[player_id].remove(queue)
        log.debug("%s: Player deregisters", player_id)
        if not self.player_queues[player_id]:
            log.debug("%s: all queues gone", player_id)
            self.deregister_actor(player_id)
            self.players.pop(player_id)
            self.player_queues.pop(player_id)
            return True
        else:
            return False
