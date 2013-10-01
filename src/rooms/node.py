#!/usr/bin/env python

from gevent import monkey
monkey.patch_socket()

import os
import uuid

import gevent

from rooms.node_controller import NodeController
from rooms.mongo.mongo_container import MongoContainer
from rooms.container import Container
from rooms.player_actor import PlayerActor
from rooms.save_manager import SaveManager
from rooms.null import Null
from rooms.script_wrapper import _script_listener

from geography.pointmap_geography import PointmapGeography
from geography.linearopen_geography import LinearOpenGeography

import sys

from rooms.config import config

from wsgi_server import WSGIServer

import logging
log = logging.getLogger("rooms.node")


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
        self.container = None
        self.client = None
        self.server = Null()

        self.players = dict()
        self.admins = dict()
        self.areas = dict()
        self.games = dict()
        self.game_script = None
        self.player_script = None

        self.save_manager = None

    def _get_game(self, game_id):
        if game_id not in self.games:
            self.games[game_id] = self.container.load_game(game_id)
        return self.games[game_id]

    def init_container(self, dbhost, dbport):
        config.read(os.path.join(self.game_root, "game.conf"))

        sys.path.append(config.get("scripts", "root"))

        self.game_script = config.get("scripts", "game_script")
        self.player_script = config.get("scripts", "player_script")

        mongo_container = MongoContainer(dbhost, dbport,
            config.get("game", "dbname"))
        mongo_container.init_mongo()
        # Wee bit circular
        self.save_manager = SaveManager(self, self.container)
        self.container = Container(mongo_container,
            geogs[config.get("game", "geography")](), self.save_manager)
        self.save_manager.container = self.container
        self.start_script_listener()

    def join_cluster(self, options):
        ctype = config.get("game", "controller")
        mhost, mport = options.controller_address.split(':')
        host, port = options.controller_api.split(':')
        self.client = NodeController(self, host, int(port), mhost, int(mport))
        self.client.init()

        self.client.register_with_master()

        self.client.start()

        self.save_manager.start()

    def start(self):
        self.server = WSGIServer(self.host, self.port, self)
        self.server.serve_forever()

    def manage_area(self, game_id, area_id):
        self.areas[game_id, area_id] = self.container.load_area(game_id,
            area_id)
        self.areas[game_id, area_id].node = self
        self.areas[game_id, area_id].game = self._get_game(game_id)
        # kickoff maybe

    def player_joins(self, game_id, area_id, player):
        log.debug("Player joins: %s at %s", player, area_id)
        player_id = player.username
        player_actor = self.areas[game_id, area_id].rooms[player.room_id].actors.get(player.actor_id)
        if (game_id, player_id) not in self.players and not player_actor:
            self.players[game_id, player_id] = dict(connected=False,
                token=self._create_token("%s_%s" % (game_id, player_id)))

            actor = PlayerActor(player)
            actor.server = self.server
            player.actor_id = actor.actor_id
            actor.name = player.username
            game = self._get_game(game_id)
            self.container.save_player(player)
            actor.load_script(self.player_script)
            self.players[game_id, player_id]['player'] = actor
            area = self.areas[game_id, player.area_id]
            area.rooms[player.room_id].put_actor(actor)
            if "created" in actor.script:
                actor.script.created(actor)
            actor.kick()

            log.info("Player joined: %s", player_id)
        elif player_actor:
            player_actor.server = self.server
            self.players[game_id, player_id] = dict(connected=False,
                token=self._create_token("%s_%s" % (game_id, player_id)))
            self.players[game_id, player_id]['player'] = player_actor
            log.debug("Player already in room: %s", player_id)
        else:
            log.debug("Player already here: %s", player_id)
        return dict(token=self.players[game_id, player_id]['token'])

    def admin_joins(self, username, game_id, area_id, room_id):
        log.debug("Admin joins: %s at %s / %s / %s", username, game_id, area_id,
            room_id)
        token=self._create_token(username + "ADMIN")
        self.admins[game_id, username] = dict(connected=False, token=token,
            game_id=game_id, area_id=area_id, room_id=room_id)
        return dict(token=token)

    def is_admin_token(self, token):
        for admin in self.admins.values():
            if token == admin['token']:
                return True
        return False

    def _create_token(self, token_salt):
        return token_salt

    def admin_by_token(self, token):
        for (game_id, username), admin in self.admins.items():
            if admin['token'] == token:
                return game_id, username
        return None, None

    def player_by_token(self, token):
        for player in self.players.values():
            if player['token'] == token:
                return player['player']
        return None

    def deregister(self, game_id, player_id):
        log.debug("Deregistering %s %s", game_id, player_id)
        self.server.disconnect(game_id, player_id)
        self.players.pop(game_id, player_id)
        log.info("Player left: %s %s", game_id, player_id)

    def shutdown(self):
        if self.client:
            self.client.deregister_from_master()
        if self.save_manager:
            self.save_manager.shutdown()

    def call(self, game_id, player_id, command, kwargs):
        actor = self.players[game_id, player_id]['player']
        if command == "api":
            return actor.api()
        else:
            return actor.call_command(command, **kwargs)

    def actor_request(self, player_id, actor_id, command, kwargs):
        player = self.players[player_id]['player']
        actor = player.room.actors[actor_id]
        if command == "api":
            return actor.api()
        else:
            return actor.call_request(command, player, **kwargs)

    def kill_player(self, player_actor):
        actor_id = player_actor.actor_id
        player = player_actor.player
        player.game_id = None
        player.room_id = None
        player.actor_id = None
        player.area_id = None
        self.container.save_player(player)
        self.server.send_update(player.username, 'kill')
        self.deregister(player.username, player.game_id)

    def move_actors_to_limbo(self, exit_area_id, exit_room_id, actors):
        self.container.save_actors_to_limbo(exit_area_id, exit_room_id, actors)

    def load_from_limbo(self, game_id, area_id):
        limbos = self.container.load_limbos_for(game_id, area_id)
        for limbo in limbos:
            area = self.areas[game_id, area_id]
            room = area.rooms[limbo.room_id]
            actors = dict([(actor.actor_id, actor) for actor in \
                limbo.actors])
            for actor_id, actor in actors.items():
                if actor._docked_with_id:
                    actors[actor._docked_with_id].dock(actor)
                room.put_actor(actor, actor.position())
            for actor_id, actor in actors.items():
                actor.kick()
        self.container.remove_limbos_for(game_id, area_id)

    def send_message(self, from_actor_id, game_id, actor_id, room_id, area_id,
            message):
        if area_id in self.areas:
            self.areas[game_id, area_id].rooms[room_id].actors[actor_id].message_received(
                from_actor_id, message)
        else:
            self.master.send_message(from_actor_id=from_actor_id,
                actor_id=actor_id, game_id=game_id, area_id=area_id,
                room_id=room_id, message=message)

    def start_script_listener(self):
        gevent.spawn(_script_listener)

    def stop_game_gthreads(self, game_id):
        for (g_id, a_id), area in self.areas.items():
            for room_id, room in area.rooms._rooms.items():
                for actor_id, actor in room.actors.items():
                    actor.kill_gthread()
                    actor._kill_move_gthread()

    def remove_areas(self, game_id):
        for g_id, a_id in self.areas.keys():
            if g_id == game_id:
                self.areas.pop((g_id, a_id))
