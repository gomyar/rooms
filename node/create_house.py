#!/usr/bin/python

from container import *
from container import _encode

init_mongo()

area = Area()
area.area_name = "mansion"
area.owner_id = 1

foyer = Room('foyer', (820, 1480), 420, 520, description="The Foyer")
area.rooms['foyer'] = foyer
#lobby.add_object(RoomObject(200, 200), (300, 300))

cloakroom = Room('cloakroom', (280, 1440), 520, 320, description="The Cloakroom")
area.rooms['cloakroom'] = cloakroom

trophyroom = Room('trophyroom', (1260, 1440), 460, 320, description="The Trophy Room")
area.rooms['trophyroom'] = trophyroom

hall = Room('hall', (940, 820), 200, 640, description="The Hall")
area.rooms['hall'] = hall

lounge = Room('lounge', (420, 1000), 500, 420, description="The Lounge")
area.rooms['lounge'] = lounge

library = Room('library', (1160, 920), 460, 500, description="The Library")
area.rooms['library'] = library

kitchen = Room('kitchen', (340, 460), 420, 520, description="The Kitchen")
area.rooms['kitchen'] = kitchen

study = Room('study', (1240, 580), 520, 320, description="The Study")
area.rooms['study'] = study

diningroom = Room('diningroom', (780, 60), 440, 740, description="The Dining Room")
area.rooms['diningroom'] = diningroom

pantry = Room('pantry', (340, 60), 420, 380, description="The Pantry")
area.rooms['pantry'] = pantry

billiardroom = Room('billiardroom', (1240, 200), 500, 360, description="The Billiard Room")
area.rooms['billiardroom'] = billiardroom


area.create_door(foyer, cloakroom, (820, 1580), (800, 1580))
area.create_door(foyer, trophyroom, (1240, 1580), (1260, 1580))
area.create_door(foyer, hall, (1040, 1480), (1040, 1460))
area.create_door(hall, diningroom, (1040, 820), (1040, 800))
area.create_door(hall, library, (1120, 1080), (1140, 1080))
area.create_door(hall, lounge, (940, 1240), (920, 1240))
area.create_door(lounge, kitchen, (520, 1000), (520, 980))
area.create_door(diningroom, kitchen, (780, 600), (760, 600))
area.create_door(kitchen, pantry, (460, 460), (460, 440))
area.create_door(study, diningroom, (1240, 680), (1220, 680))
area.create_door(study, billiardroom, (1600, 580), (1600, 560))
area.create_door(library, study, (1420, 920), (1420, 900))

area.entry_point_room_id = "foyer"

area.add_npc(NpcActor("butler"), 'foyer')
area.add_npc(NpcActor("dilettante"), 'study')
area.add_npc(NpcActor("gladys"), 'diningroom')
area.add_npc(NpcActor("jezabel"), 'diningroom')
area.add_npc(NpcActor("major"), 'trophyroom')
area.add_npc(NpcActor("professor"), 'library')
area.add_npc(NpcActor("aunt"), 'lounge')

save_area(area)
