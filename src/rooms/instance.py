
import time
import random

import gevent.queue
import simplejson

from actor import Actor
from player_actor import PlayerActor
import rooms.container

import logging
log = logging.getLogger("rooms.instance")

class Instance:
    def __init__(self, uid=None, node=None):
        self.uid = uid
        self.player_queues = dict()
        self.players = dict()
        self.area = None
        self.node = node

    def load_area(self, area_id):
        self.area = self.node.container.load_area(area_id)
        self.area.instance = self

    def sleep(self):
        print "Sleeping instance"

    def call(self, command, player_id, actor_id, kwargs):
        player = self.players[player_id]['player']
        actor = player.room.actors[actor_id]
        if player == actor:
            if command == "exposed_commands":
                return actor.exposed_commands()
            value = actor.command_call(command, **kwargs)
        else:
            if command == "exposed_methods":
                return actor.exposed_methods(player)
            value = actor.interface_call(command, player, **kwargs)
        return value

    def send_update(self, player_id, command, **kwargs):
        if player_id in self.player_queues:
            self.player_queues[player_id].put(dict(command=command,
                kwargs=kwargs))

    def send_to_all(self, command, **kwargs):
        for queue in self.player_queues.values():
            queue.put(dict(command=command, kwargs=kwargs))

    def send_to_players(self, player_ids, command, **kwargs):
        for player_id in player_ids:
            self.send_update(player_id, command, **kwargs)

    def send_sync(self, player_id):
        self.player_queues[player_id].put(self.sync(player_id))

    def sync(self, player_id):
        player = self.players[player_id]['player']
        return {
            "command": "sync",
            "kwargs" : {
                "actors" : map(lambda a: a.external(player),
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
        queue = gevent.queue.Queue()
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
        self.area.player_joined_instance(actor, self.area.entry_point_room_id)
        self.send_to_all("player_joined_instance", actor_id=player_id)
        if actor.script and actor.script.has_method("player_created"):
            actor._wrapped_call("player_created", actor)
        actor.start_command_processor()

        log.info("Player joined instance: %s", player_id)

    def deregister(self, player_id):
        self.disconnect(player_id)
        actor = self.players[player_id]['player']
        self.area.actor_left_instance(actor)
        self.send_to_all("actor_left_instance", actor_id=player_id)
        self.players.pop(player_id)
        self.node.controller.player_left(player_id, self.uid)

        log.info("Player left instance: %s", player_id)

    def kickoff(self):
        for room_id in self.area.rooms._room_map.keys():
            room = self.area.rooms[room_id]
            for npc in room.all_npcs():
                npc.start_command_processor()
        self.area.rebuild_area_map()
        print "Pointless kickoff call"
