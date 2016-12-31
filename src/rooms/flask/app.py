
import os

import logging
import logging.config
log = logging.getLogger("rooms")

from rooms.mongo_master import Master
from rooms.mongo_node import Node
from rooms.geography.basic_geography import BasicGeography
from rooms.room_builder import RoomBuilder
from rooms.room_builder import FileMapSource
from rooms.container import Container
from rooms.dbase.mongo_dbase import MongoDBase
from rooms.item_registry import ItemRegistry


if os.path.exists(os.path.join(options.game, "logging.conf")):
    logging.config.fileConfig(os.path.join(options.game,
        "logging.conf"))
else:
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

_mongo_host = os.environ.get('ROOMS_MONGO_HOST', 'localhost')
_mongo_port = int(os.environ.get('ROOMS_MONGO_PORT', '27017'))
_mongo_dbname = os.environ.get('ROOMS_MONGO_DBNAME', 'rooms')

_node_hostname = os.environ.get('ROOMS_NODE_HOSTNAME', 'localhost')

_rooms_projectdir = os.environ.get('ROOMS_PROJECTDIR', '.')

dbase = MongoDBase(host=_mongo_host, port=_mongo_port, dbname=_mongo_dbname)
dbase.init_mongo()

container = Container(dbase, None)
node = Node(container, _node_hostname, _node_hostname)
container.node = node
room_builder = RoomBuilder(FileMapSource(os.path.join(_rooms_projectdir,
    "maps")), node)
item_registry = ItemRegistry()
item_registry.load_from_directory(_rooms_projectdir)
container.geography = BasicGeography()
container.room_builder = room_builder
container.item_registry = item_registry
container.start_container()
master = Master(container)
master.load_scripts(os.path.join(_rooms_projectdir, "scripts"))

node.container = container
node.load_scripts(os.path.join(_rooms_projectdir, "scripts"))
