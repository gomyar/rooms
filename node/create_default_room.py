#!/usr/bin/python

from container import *
from container import _encode

init_mongo()

area = Area()
area.area_name = "default"
area.owner_id = 1

lobby = Room('lobby', (0, 0), 500, 500)

foyer = Room('foyer', (500, -300), 800, 800)

area.rooms['lobby'] = lobby

area.rooms['foyer'] = foyer

area.create_door(lobby, foyer, (500, 250), (0, 250))

area.entry_point_room_id = "lobby"
area.entry_point_door_id = "door_foyer_500_250"

save_area(area)
