#!/usr/bin/python

from container import *
from container import _encode

init_mongo()

area = Area()
area.area_name = "mansion"
area.owner_id = 1

foyer = Room('foyer', (410, 740), 210, 260, description="The Foyer")
area.rooms['foyer'] = foyer
#lobby.add_object(RoomObject(200, 200), (300, 300))

cloakroom = Room('cloakroom', (140, 720), 260, 160, description="The Cloakroom")
area.rooms['cloakroom'] = cloakroom

trophyroom = Room('trophyroom', (630, 720), 230, 160, description="The Trophyroom")
area.rooms['trophyroom'] = trophyroom

hall = Room('hall', (460, 410), 90, 320, description="The Hall")
area.rooms['hall'] = hall

lounge = Room('lounge', (210, 500), 250, 210, description="The Lounge")
area.rooms['lounge'] = lounge

library = Room('library', (570, 460), 230, 250, description="The Library")
area.rooms['library'] = library

kitchen = Room('kitchen', (170, 230), 210, 260, description="The Kitchen")
area.rooms['kitchen'] = kitchen

study = Room('study', (620, 290), 260, 160, description="The Study")
area.rooms['study'] = study

diningroom = Room('diningroom', (390, 30), 220, 370, description="The Diningroom")
area.rooms['diningroom'] = diningroom

pantry = Room('pantry', (170, 30), 210, 190, description="The Pantry")
area.rooms['pantry'] = pantry

billiardroom = Room('billiardroom', (620, 100), 250, 180, description="The Billiardroom")
area.rooms['billiardroom'] = billiardroom


area.create_door(foyer, cloakroom, (410, 790), (400, 790))
area.create_door(foyer, trophyroom, (620, 790), (630, 790))
area.create_door(foyer, hall, (510, 730), (510, 720))
area.create_door(hall, diningroom, (510, 410), (510, 400))
area.create_door(hall, library, (560, 540), (570, 540))
area.create_door(hall, lounge, (460, 620), (450, 620))
area.create_door(lounge, kitchen, (260, 500), (260, 490))
area.create_door(diningroom, kitchen, (390, 300), (380, 300))
area.create_door(kitchen, pantry, (230, 230), (220, 230))
area.create_door(study, diningroom, (620, 340), (610, 340))
area.create_door(study, billiardroom, (800, 290), (800, 280))
area.create_door(library, study, (710, 460), (710, 450))

area.entry_point_room_id = "foyer"

save_area(area)
