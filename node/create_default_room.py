#!/usr/bin/python

from container import *
from container import _encode

init_mongo()

area = Area()
area.area_name = "default"
area.owner_id = 1

lobby = Room('lobby', (0, 0), 500, 500)
lobby.add_object(RoomObject(150, 150), (20, 20))
lobby.add_object(RoomObject(150, 150), (330, 20))
lobby.add_object(RoomObject(250, 125), (125, 100))

foyer = Room('foyer', (500, -300), 800, 800)
foyer.add_object(RoomObject(200, 200), (300, 300))

area.rooms['lobby'] = lobby

area.rooms['foyer'] = foyer

area.create_door(lobby, foyer, (500, 250), (500, 250))

area.entry_point_room_id = "lobby"
area.entry_point_door_id = "door_foyer_500_250"

save_area(area)
