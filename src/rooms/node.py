#!/usr/bin/env python

from gevent import monkey
monkey.patch_socket()

import os

import uuid

from controller import MasterController
from controller import ClientController

from rooms.instance import Instance
from rooms.settings import settings

from rooms.mongo.mongo_container import MongoContainer

import sys

from ConfigParser import ConfigParser

from wsgi_server import WSGIServer

import logging
log = logging.getLogger("rooms.node")


class Node(object):
    def __init__(self, game_root, host, port):
        self.game_root = game_root
        self.host = host
        self.port = port
        self.controller = None
        self.controller_stub = None
        self.admin_controller = None
        self.container = None
        self.config = None
        self.client = None

        self.instances = dict()
        self.sessions = dict()

    def load_game(self, dbhost, dbport):
        self.config = ConfigParser()
        self.config.read(os.path.join(self.game_root, "game.conf"))
        script_dir = self.config.get("scripts", "root")
        sys.path.append(script_dir)
        settings['script_dir'] = script_dir

        self.container = MongoContainer(dbhost, dbport)
        self.container.init_mongo()

    def init_controller(self, options):
        mhost, mport = options.controller_address.split(':')
        self.master = MasterController(self.config, mhost, int(mport),
            self.container)
        self.master.init()
        host, port = options.controller_api.split(':')
        self.client = ClientController(self, host, int(port), mhost, int(mport))
        self.client.init()

        self.master.register_node(host, port, self.host, self.port)

        self.master.start()
        self.client.start()

    def start(self):
        self.server = WSGIServer(self.host, self.port, self)
        self.server.serve_forever()

    def manage_area(self, area_id):
        uid = self._random_uid()
        instance = Instance(uid, self)
        instance.load_area(area_id)
        self.instances[uid] = instance
        instance.kickoff()
        return uid

    def player_joins(self, instance_uid, player_id):
        instance = self.instances[instance_uid]
        instance.register(player_id)

    def shutdown(self):
        if self.client:
            self.client.deregister_from_master()

    def _random_uid(self):
        return str(uuid.uuid1())
