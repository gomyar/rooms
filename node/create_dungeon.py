#!/usr/bin/python
import sys

from container import *
from container import _encode
from rooms.actor import *


from scripts.DungeonScript import DungeonScript

init_mongo()

area = Area()
area.rooms = MongoRoomContainer(area)
area.area_name = "dungeon"
area.owner_id = 1

entrance = Room('entrance', (0, 0), 390, 390, description="Entrance")
area.entry_point_room_id = "entrance"
area.add_room(entrance)

area.game_script = load_script("DungeonScript")

def _create_room(area, x, y, from_room):
    room_id = "%s,%s" % (x, y)
    room = Room(room_id, (x * 400, y * 400), 390, 390,
        description=room_id)
    area.add_room(room)
    area.create_door(room, from_room)
    return room


room1 = _create_room(area, 0, 1, area.rooms['entrance'])
room2 = _create_room(area, 0, 2, room1)
room3 = _create_room(area, 0, 3, room2)

room4 = _create_room(area, 0, -1, area.rooms['entrance'])
room5 = _create_room(area, 0, -2, room4)
room6 = _create_room(area, 0, -3, room5)

room7 = _create_room(area, 1, 0, area.rooms['entrance'])
room8 = _create_room(area, 2, 0, room7)
room9 = _create_room(area, 3, 0, room8)

room10 = _create_room(area, -1, 0, area.rooms['entrance'])
room11 = _create_room(area, -2, 0, room10)
room12 = _create_room(area, -3, 0, room11)



save_area(area)
