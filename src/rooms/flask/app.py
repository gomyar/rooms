
import os
import traceback
import uuid
import socket

import logging
import logging.config
log = logging.getLogger("rooms")

from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from werkzeug.debug import DebuggedApplication
from decouple import Config, RepositoryEnv

from rooms.master import Master
from rooms.node import Node
from rooms.geography.basic_geography import BasicGeography
from rooms.room_builder import RoomBuilder
from rooms.room_builder import FileMapSource
from rooms.container import Container
from rooms.dbase.mongo_dbase import MongoDBase
from rooms.item_registry import ItemRegistry

config = Config(RepositoryEnv(os.environ.get('ROOMS_CONFIG', os.path.join(
    os.getcwd(), 'game.env'))))


_mongo_host = config('ROOMS_MONGO_HOST', default='localhost')
_mongo_port = config('ROOMS_MONGO_PORT', default='27017', cast=int)
_mongo_dbname = config('ROOMS_MONGO_DBNAME', default='rooms')

_node_name = config('ROOMS_NODE_NAME', default='local')
_node_host = config('ROOMS_NODE_HOST', default=socket.gethostname())
_node_port = config('ROOMS_NODE_PORT', default=5000, cast=int)
_node_hostname = config('ROOMS_NODE_HOSTNAME', default='%s:%s' % (
    _node_host, _node_port))

_rooms_projectdir = config('ROOMS_PROJECTDIR', default=os.getcwd())

_logging_conf = config('LOGGING_CONF', default=os.path.join(_rooms_projectdir,
                                                            "logging.conf"))

mapdir = os.path.join(_rooms_projectdir, "maps")
itemdir = os.path.join(_rooms_projectdir, "items")


if os.path.exists(_logging_conf):
    logging.config.fileConfig(_logging_conf)
else:
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


dbase = MongoDBase(host=_mongo_host, port=_mongo_port, dbname=_mongo_dbname)
dbase.init_mongo()

container = Container(dbase, None)
node = Node(container, _node_name, _node_hostname)
container.node = node
container.player_script_name = "scripts.player_script"
container.room_script_name = "scripts.room_script"
room_builder = RoomBuilder(FileMapSource(mapdir), node)
item_registry = ItemRegistry()
if os.path.exists(itemdir):
    item_registry.load_from_directory(itemdir)
container.geography = BasicGeography()
container.room_builder = room_builder
container.item_registry = item_registry
container.start_container()

master = Master(container)
node.container = container


def start_rooms_app(app):
    try:
        container.start_container()

        http_server = WSGIServer((_node_host, _node_port), app,
                                 handler_class=WebSocketHandler)
        http_server.serve_forever()
    except KeyboardInterrupt, ke:
        log.debug("Server interrupted")
        node.shutdown()
        master.shutdown()
        container.stop_container()
    except:
        traceback.print_exc()
        log.exception("Exception starting server")
