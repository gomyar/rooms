#!/usr/bin/python
import sys

from rooms.container import *
from rooms.container import _encode
from rooms.actor import *

from script import create_npc


init_mongo()

area = Area()
area.rooms = MongoRoomContainer(area)
area.area_name = "mansion"
area.owner_id = 1

# Foyer
foyer = Room('foyer', (820, 1480), 420, 430, description="The Foyer")
foyer.add_object("t1",
    RoomObject("marble_side_table", 90, 90), (50, 10))
foyer.add_object("t2",
    RoomObject("marble_side_table", 90, 90), (300, 340))
foyer.add_object("sofa",
    RoomObject("couch_east", 50, 190), (0, 200))
foyer.add_object("painting",
    RoomObject("large_painting_west", 10, 190), (410, 190))
area.rooms['foyer'] = foyer

# Cloackroom
cloakroom = Room('cloakroom', (280, 1440), 520, 320, description="The Cloakroom")
area.rooms['cloakroom'] = cloakroom

# Trophyroom
trophyroom = Room('trophyroom', (1260, 1440), 460, 320, description="The Trophy Room")
area.rooms['trophyroom'] = trophyroom

# Hall
hall = Room('hall', (940, 820), 200, 640, description="The Hall")
area.rooms['hall'] = hall

# Lounge
lounge = Room('lounge', (420, 1000), 500, 420, description="The Lounge")
area.rooms['lounge'] = lounge

# Library
library = Room('library', (1160, 920), 460, 500, description="The Library")
area.rooms['library'] = library

# Kitchen
kitchen = Room('kitchen', (340, 460), 420, 520, description="The Kitchen")
area.rooms['kitchen'] = kitchen

# Study
study = Room('study', (1240, 580), 520, 320, description="The Study")
area.rooms['study'] = study

# Diningroom
diningroom = Room('diningroom', (780, 60), 440, 740, description="The Dining Room")
diningroom.add_object("diningroom_table",
    RoomObject("diningroom_table", 160, 350), (160, 160))
diningroom.add_object("diningroom_chair_l1",
    RoomObject("diningroom_chair_right", 40, 60, facing=FACING_EAST), (120, 190))
diningroom.add_object("diningroom_chair_l2",
    RoomObject("diningroom_chair_right", 40, 60, facing=FACING_EAST), (120, 270))
diningroom.add_object("diningroom_chair_l3",
    RoomObject("diningroom_chair_right", 40, 60, facing=FACING_EAST), (120, 350))
diningroom.add_object("diningroom_chair_l4",
    RoomObject("diningroom_chair_right", 40, 60, facing=FACING_EAST), (120, 420))

diningroom.add_object("diningroom_table",
    RoomObject("diningroom_table", 160, 350), (160, 160))
diningroom.add_object("diningroom_chair_r1",
    RoomObject("diningroom_chair_left", 40, 60, facing=FACING_WEST), (320, 190))
diningroom.add_object("diningroom_chair_r2",
    RoomObject("diningroom_chair_left", 40, 60, facing=FACING_WEST), (320, 270))
diningroom.add_object("diningroom_chair_r3",
    RoomObject("diningroom_chair_left", 40, 60, facing=FACING_WEST), (320, 350))
diningroom.add_object("diningroom_chair_r4",
    RoomObject("diningroom_chair_left", 40, 60, facing=FACING_WEST), (320, 420))

diningroom.add_object("diningroom_chair_t1",
    RoomObject("diningroom_chair_down", 60, 40, facing=FACING_SOUTH), (220, 120))
diningroom.add_object("diningroom_chair_b1",
    RoomObject("diningroom_chair_up", 60, 40, facing=FACING_NORTH), (220, 510))

area.rooms['diningroom'] = diningroom

# Pantry
pantry = Room('pantry', (340, 60), 420, 380, description="The Pantry")
area.rooms['pantry'] = pantry

# Billiardroom
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

area.game_script = load_script("MansionGameScript")

create_npc(area, "butler", "ButlerScript", 'foyer')
create_npc(area, "dilettante", "DilettanteScript", 'study')
create_npc(area, "gladys", "GladysScript", 'diningroom')
create_npc(area, "jezabel", "JezabelScript", 'diningroom')
create_npc(area, "major", "MajorScript", 'trophyroom')
create_npc(area, "professor", "ProfessorScript", 'library')
create_npc(area, "aunt", "AuntScript", 'lounge')

save_area(area)
