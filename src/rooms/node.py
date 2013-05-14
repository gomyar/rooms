#!/usr/bin/env python

from gevent import monkey
monkey.patch_socket()

import os

import uuid

import controller
from controller import instanced_controller
from controller import massive_controller

from rooms.mongo.mongo_container import MongoContainer
from rooms.container import Container
from rooms.player_actor import PlayerActor
from rooms.save_manager import SaveManager
from rooms.null import Null
from rooms.inventory import set_registry

from geography.pointmap_geography import PointmapGeography
from geography.linearopen_geography import LinearOpenGeography

import sys

from rooms.config import config

from wsgi_server import WSGIServer

import logging
log = logging.getLogger("rooms.node")


controller_types = {
    'instanced_master': instanced_controller.MasterController,
    'instanced_client': instanced_controller.ClientController,
    'massive_master': massive_controller.MasterController,
    'massive_client': massive_controller.ClientController,
}

geogs = {
    'pointmap': PointmapGeography,
    'linearopen': LinearOpenGeography,
}


class Node(object):
    def __init__(self, game_root, host, port):
        self.game_root = game_root
        self.host = host
        self.port = port
        self.controller = None
        self.controller_stub = None
        self.admin_controller = None
        self.container = None
        self.client = None
        self.game = None
        self.server = Null()

        self.players = dict()
        self.areas = dict()

        self.save_manager = None

    def load_game(self, dbhost, dbport):
        config.read(os.path.join(self.game_root, "game.conf"))

        sys.path.append(config.get("scripts", "root"))

        mongo_container = MongoContainer(dbhost, dbport)
        mongo_container.init_mongo()
        # Wee bit circular
        self.save_manager = SaveManager(self, self.container)
        self.container = Container(mongo_container,
            geogs[config.get("game", "geography")](), self.save_manager)
        self.save_manager.container = self.container
        self.game = self.container.load_game(config.get("game", "game_id"))
        set_registry(self.game.item_registry)


    def init_controller(self, options):
        ctype = config.get("game", "controller")
        master = controller_types["%s_master" % (ctype,)]
        client = controller_types["%s_client" % (ctype,)]
        mhost, mport = options.controller_address.split(':')
        self.master = master(self, mhost, int(mport), self.container)
        self.master.init()
        host, port = options.controller_api.split(':')
        self.client = client(self, host, int(port), mhost, int(mport))
        self.client.init()

        self.master.register_node(host, port, self.host, self.port)

        self.master.start()
        self.client.start()

        self.save_manager.start()

    def join_cluster(self, options):
        ctype = config.get("game", "controller")
        client = controller_types["%s_client" % (ctype,)]
        mhost, mport = options.controller_address.split(':')
        host, port = options.controller_api.split(':')
        self.client = client(self, host, int(port), mhost, int(mport))
        self.client.init()

        self.client.register_with_master()

        self.client.start()

        self.save_manager.start()

    def start(self):
        self.server = WSGIServer(self.host, self.port, self)
        self.server.serve_forever()

    def manage_area(self, area_id):
        self.areas[area_id] = self.container.load_area(area_id)
        self.areas[area_id].game = self.game
        self.areas[area_id].node = self
        # kickoff maybe

    def player_joins(self, area_id, player):
        log.debug("Player joins: %s at %s", player, area_id)
        player_id = player.username
        player_actor = self.areas[area_id].rooms[player.room_id].actors.get(player.actor_id)
        if player_id not in self.players and not player_actor:
            self.players[player_id] = dict(connected=False,
                token=self._create_token(player_id))

            actor = PlayerActor(player)
            actor.server = self.server
            player.actor_id = actor.actor_id
            actor.name = player.username
            self.container.save_player(player)
            if self.game.player_script:
                actor.load_script(self.game.player_script)
            self.players[player_id]['player'] = actor
            area = self.areas[player.area_id]
            area.rooms[player.room_id].put_actor(actor)
            if "created" in actor.script:
                actor.script.created(actor)
            actor.kick()

            log.info("Player joined: %s", player_id)
        elif player_actor:
            player_actor.server = self.server
            self.players[player_id] = dict(connected=False,
                token=self._create_token(player_id))
            self.players[player_id]['player'] = player_actor
            log.debug("Player already in room: %s", player_id)
        else:
            log.debug("Player already here: %s", player_id)
        return dict(token=self.players[player_id]['token'])

    def _create_token(self, player_id):
        return player_id

    def player_by_token(self, token):
        for player in self.players.values():
            if player['token'] == token:
                return player['player']
        return None

    def deregister(self, player_id):
        log.debug("Deregistering %s", player_id)
        self.server.disconnect(player_id)
        self.players.pop(player_id)
        log.info("Player left: %s", player_id)

    def shutdown(self):
        if self.client:
            self.client.deregister_from_master()
        if self.save_manager:
            self.save_manager.shutdown()

    def find(self, player_id):
        for area in self.area.values():
            for room in area.rooms._rooms.values():
                if player_id in room.actors:
                    return room.actors[player_id]
        return None

    def call(self, player_id, command, kwargs):
        actor = self.players[player_id]['player']
        if command == "api":
            return actor.api()
        else:
            return actor.call_command(command, **kwargs)

    def kill_player(self, player_actor):
        actor_id = player_actor.actor_id
        player = player_actor.player
        player.room_id = None
        player.actor_id = None
        player.area_id = None
        self.container.save_player(player)
        self.server.send_update(player.username, 'kill')
        self.deregister(player.username)

    def move_actors_to_limbo(self, exit_area_id, exit_room_id, actors):
        self.container.save_actors_to_limbo(exit_area_id, exit_room_id, actors)

    def load_from_limbo(self, area_id):
        limbos = self.container.load_limbos_for(area_id)
        for limbo in limbos:
            area = self.areas[area_id]
            room = area.rooms[limbo.room_id]
            actors = dict([(actor.actor_id, actor) for actor in \
                limbo.actors])
            for actor_id, actor in actors.items():
                if actor._docked_with_id:
                    actors[actor._docked_with_id].dock(actor)
#                if actor.parents:
#                    actors[actor.parents[0]].dock(actor)
                room.put_actor(actor, actor.position())
            for actor_id, actor in actors.items():
                actor.kick()
        self.container.remove_limbos_for(area_id)

    def send_message(self, actor_id, room_id, area_id, message):
        if area_id in self.areas:
            self.areas[area_id].rooms[room_id].actors[actor_id].message_received(
                message)
        else:
            self.master.send_message(actor_id=actor_id, room_id=room_id,
                area_id=area_id, message=message)
