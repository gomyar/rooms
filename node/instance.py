
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
        map_url = "%s.json" % (map_id,)
        self.area = container.load_area(map_url)

    def call(self, command, player_id, actor_id, kwargs):
        player = self.players[player_id]['player']
        actor = player.room.actors[actor_id]
        if player == actor:
            value = actor.command_call(command, **kwargs)
        else:
            value = actor.interface_call(command, player, **kwargs)
        self.send_to_all("actor_update", **actor.external())
        return value

    def player_joins(self, player_id):
        self.players[player_id] = dict(connected=False)
        log.debug("Player joined: %s", player_id)

    def create_instance(self, map_id):
        log.debug("Instance created %s", map_id)

    def register_actor(self, player_id, room_id='lobby', door_id='entrance'):
        if player_id in self.area.actors:
            self.deregister_actor(player_id)

        actor = PlayerActor(player_id, 10, 10)
        self.players[player_id]['player'] = actor
        self.players[player_id]['connected'] = True
        self.area.actors[player_id] = actor
        actor.instance = self
        self.area.actor_enters(actor, room_id, door_id)
        self.send_to_all("actor_joined", **actor.external())

    def deregister_actor(self, player_id):
        if player_id in self.area.actors:
            actor = self.area.actors.pop(player_id)
            self.area.actor_exits(actor)
            self.send_to_all("actor_left", player_id=player_id)

    def send_message(self, player_id, msg):
        self.queues[player_id].put(dict(command="log", kwargs={'msg': msg}))

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
