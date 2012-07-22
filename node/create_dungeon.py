#!/usr/bin/python
import sys

from container import *
from container import _encode
from actor import *


from scripts.DungeonScript import DungeonScript

init_mongo()

area = Area()
area.rooms = MongoRoomContainer()
area.area_name = "dungeon"
area.owner_id = 1

entrance = Room('entrance', (0, 0), 390, 390, description="Entrance")
area.entry_point_room_id = "entrance"
area.rooms['entrance'] = entrance

area.game_script = load_script("DungeonScript")

save_area(area)
