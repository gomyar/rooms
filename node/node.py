#!/usr/bin/env python

from gevent import monkey
monkey.patch_socket()

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import time
import os

from optparse import OptionParser

import xmlrpclib

import uuid

import urlparse
from mimetypes import guess_type

import simplejson

from instance_controller import InstanceController

from rooms.instance import Instance
from rooms.admin import Admin
from rooms.settings import settings

from gevent.queue import Empty

from mongo_container import MongoContainer

import signal
import sys

from ConfigParser import ConfigParser

from wsgi_server import WSGIServer
from instance_controller import NodeStub


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

    def init_controller(self, controller_address):
        if options.controller_address:
            log.info("Connecting to Controller at %s",
                options.controller_address)
            self.register_with_controller(options.controller_address)
        else:
            log.info("Assuming Controller role")
            self.controller = InstanceController()
            stub = NodeStub(self.host, self.port)
            stub.create_instance = self.create_instance
            stub.player_joins = self.player_joins
            self.controller.nodes[(self.host, self.port)] = stub

    def register_with_controller(self, controller_address):
        self.controller = xmlrpclib.ServerProxy('http://%s' % (
            controller_address,))
        self.controller.register_node(self.host, self.port)

    def deregister_from_controller(self):
        if self.controller:
            self.controller.deregister_node(self.host, self.port)

    def start(self):
        self.server = WSGIServer(self)
        self.server.serve_forever()

    def create_instance(self, map_id):
        uid = str(uuid.uuid1())
        instance = Instance(uid, self)
        instance.load_map(map_id)
        self.instances[uid] = instance
        instance.kickoff()
        return uid

    def player_joins(self, instance_uid, player_id):
        instance = self.instances[instance_uid]
        instance.register(player_id)


if __name__ == "__main__":
    node = None
    try:
        log.info("Starting server")
        parser = OptionParser()

        parser.add_option("-c", "--controller", dest="controller_address",
            help="Address of controller node")

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
        node.init_controller(options.controller_address)
        node.start()
    except:
        log.exception("Exception starting server")
    finally:
        log.info("Server stopped")
        if node:
            node.deregister_from_controller()
