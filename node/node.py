#!/usr/bin/env python

from gevent import monkey
monkey.patch_socket()

import os

from optparse import OptionParser

import uuid

from instance_controller import InstanceController

from rooms.instance import Instance
from rooms.settings import settings

from mongo_container import MongoContainer

import sys

from ConfigParser import ConfigParser

from wsgi_server import WSGIServer


import logging
import logging.config
logging.config.fileConfig("logging.conf")
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

        self.instances = dict()
        self.sessions = dict()

    def load_game(self):
        config = ConfigParser()
        config.read(os.path.join(self.game_root, "game.conf"))
        script_dir = config.get("scripts", "root")
        sys.path.append(script_dir)
        settings['script_dir'] = script_dir

        node.container = MongoContainer(dbhost, int(dbport))
        node.container.init_mongo()

    def init_controller(self, options):
        self.controller = InstanceController(self)
        self.controller.init(options)

    def start(self):
        self.server = WSGIServer(host, port, self)
        self.server.serve_forever()

    def create_instance(self, area_id):
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
        self.controller.deregister_node(self.host, self.port)

    def random_uid(self):
        return str(uuid.uuid1())


if __name__ == "__main__":
    node = None
    try:
        log.info("Starting server")
        parser = OptionParser()

        parser.add_option("-c", "--controller", dest="controller_address",
            help="Address of controller node")

        parser.add_option("-i", "--controller-api", dest="controller_api",
            help="Address of controller xmlrpc api (client and controller)",
            default="localhost:8081")

        parser.add_option("-a", "--address", dest="address",
            default="localhost:8080", help="Address to serve node on")

        parser.add_option("-d", "--dbaddr", dest="dbaddr",
            default="localhost:27017", help="Address of mongo server")

        parser.add_option("-g", "--game", dest="game",
            default="/home/ray/projects/rooms/games/demo1",
                help="Path to game dir")

        (options, args) = parser.parse_args()

        host, port = options.address.split(":")
        dbhost, dbport = options.dbaddr.split(":")

        node = Node(options.game, host, int(port))
        node.load_game()
        node.init_controller(options)
        node.start()
    except:
        log.exception("Exception starting server")
    finally:
        log.info("Server stopped")
        if node:
            node.shutdown()
