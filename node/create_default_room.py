#!/usr/bin/python

from container import *
from container import _encode

init_mongo()

area = Area()
area.area_name = "default"
area.owner_id = 1

lobby = Room('lobby', (0, 0), 50, 50)

foyer = Room('foyer', (50, 0), 50, 50)

area.rooms['lobby'] = lobby

area.rooms['foyer'] = foyer

area.create_door(lobby, foyer, (50, 25), (0, 25))

area.entry_point_room_id = "lobby"
area.entry_point_door_id = "door_foyer_50_25"

save_area(area)
