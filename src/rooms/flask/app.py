
import os
import traceback
import uuid

import logging
import logging.config
log = logging.getLogger("rooms")

from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from werkzeug.debug import DebuggedApplication

from rooms.master import Master
from rooms.node import Node
from rooms.geography.basic_geography import BasicGeography
from rooms.room_builder import RoomBuilder
from rooms.room_builder import FileMapSource
from rooms.container import Container
from rooms.dbase.mongo_dbase import MongoDBase
from rooms.item_registry import ItemRegistry


_mongo_host = os.environ.get('ROOMS_MONGO_HOST', 'localhost')
_mongo_port = int(os.environ.get('ROOMS_MONGO_PORT', '27017'))
_mongo_dbname = os.environ.get('ROOMS_MONGO_DBNAME', 'rooms')

_node_hostname = os.environ.get('ROOMS_NODE_HOSTNAME', 'localhost:5000')
_node_name = os.environ.get('ROOMS_NODE_NAME', 'local')
_node_host = os.environ.get('ROOMS_NODE_HOST', 'localhost')
_node_port = int(os.environ.get('ROOMS_NODE_PORT', 5000))

_rooms_projectdir = os.environ.get('ROOMS_PROJECTDIR', os.getcwd())

mapdir = os.path.join(_rooms_projectdir, "maps")
itemdir = os.path.join(_rooms_projectdir, "items")


if os.path.exists(os.path.join(_rooms_projectdir, "logging.conf")):
    logging.config.fileConfig(os.path.join(_rooms_projectdir,
        "logging.conf"))
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
