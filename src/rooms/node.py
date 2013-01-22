#!/usr/bin/env python

from gevent import monkey
monkey.patch_socket()

import os

import uuid

import controller
from controller import instanced_controller
from controller import massive_controller

from rooms.instance import Instance
from rooms.mongo.mongo_container import MongoContainer
from rooms.container import Container

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
        self.server = None

        self.instances = dict()

    def load_game(self, dbhost, dbport):
        config.read(os.path.join(self.game_root, "game.conf"))

        sys.path.append(config.get("scripts", "root"))

        mongo_container = MongoContainer(dbhost, dbport)
        mongo_container.init_mongo()
        self.container = Container(mongo_container,
            geogs[config.get("game", "geography")](),
        )

    def init_controller(self, options):
        ctype = config.get("game", "controller")
        master = controller_types["%s_master" % (ctype,)]
        client = controller_types["%s_client" % (ctype,)]
        mhost, mport = options.controller_address.split(':')
        self.master = master(mhost, int(mport), self.container)
        self.master.init()
        host, port = options.controller_api.split(':')
        self.client = client(self, host, int(port), mhost, int(mport))
        self.client.init()

        self.master.register_node(host, port, self.host, self.port)

        self.master.start()
        self.client.start()

#        self.area_manager.start()

    def start(self):
        self.server = WSGIServer(self.host, self.port, self)
        self.server.serve_forever()

    def manage_area(self, game_id, area_id):
        self.game = self.container.load_game(game_id)
        area_uid = self.game.area_map[area_id]
        uid = self._random_uid()
        instance = Instance(uid, self)
        instance.load_area(area_uid)
        self.instances[uid] = instance
        instance.kickoff()
        return uid

    def player_joins(self, area_id, player):
        log.debug("Player joins: %s at %s", player, area_id)
        instance = self._lookup_instance(area_id)
        instance.register(player)

    def _lookup_instance(self, area_id):
        for instance_id, instance in self.instances.items():
            if area_id == instance.area.area_name:
                return instance
        raise Exception("No instance for area %s" % (area_id,))

    def shutdown(self):
        if self.client:
            self.client.deregister_from_master()

    def _random_uid(self):
        return str(uuid.uuid1())

    def find(self, player_id):
        for instance in self.instances.values():
            for room in instance.area.rooms._rooms.values():
                if player_id in room.actors:
                    return room.actors[player_id]
        return None
