#!/usr/bin/python
import sys

from rooms.container import *
from rooms.mongo.mongo_container import MongoContainer
from rooms.mongo.mongo_container import MongoRoomContainer
from rooms.actor import *
from rooms.game import Game

from rooms.script import create_npc
from rooms.script import create_item

sys.path.append("../games/demo1")

def create_game(controller):
    container = MongoContainer()
    container.init_mongo()

    game = Game()

    area = Area()
    area.rooms = MongoRoomContainer(area, container)
    area.area_name = "mansion"
    area.owner_id = "ray"
    area.load_script("demo1_script")
    area.player_script = "player_script"

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
    area.put_room(foyer, (820, 1480))

    # Cloackroom
    cloakroom = Room('cloakroom', 520, 320, description="The Cloakroom")
    area.put_room(cloakroom, (280, 1440))

    # Trophyroom
    trophyroom = Room('trophyroom', 460, 320, description="The Trophy Room")
    area.put_room(trophyroom, (1260, 1440))

    # Hall
    hall = Room('hall', 200, 640, description="The Hall")
    area.put_room(hall, (940, 820))

    # Lounge
    lounge = Room('lounge', 500, 420, description="The Lounge")

    lounge.add_object("sofa",
        RoomObject("couch_east", 50, 190), (0, 100))
    lounge.add_object("chair_up_1",
        RoomObject("diningroom_chair_up", 60, 40, facing=FACING_NORTH), (50, 380))
    lounge.add_object("t1",
        RoomObject("marble_side_table", 90, 90), (120, 330))
    lounge.add_object("chair_up_2",
        RoomObject("diningroom_chair_up", 60, 40, facing=FACING_NORTH), (220, 380))
    lounge.add_object("painting",
        RoomObject("large_painting_west", 10, 190), (550, 0))

    area.put_room(lounge, (420, 1000))

    # Library
    library = Room('library', 460, 500, description="The Library")
    library.add_object("painting",
        RoomObject("large_painting_east", 10, 190), (0, 200))
    library.add_object("sofa",
        RoomObject("couch_west", 50, 190), (410, 100))
    library.add_object("chair_up_2",
        RoomObject("diningroom_chair_up", 60, 40, facing=FACING_NORTH), (220, 460))
    library.add_object("chair_right",
        RoomObject("diningroom_chair_left", 40, 60, facing=FACING_WEST), (420, 50))
    area.put_room(library, (1140, 920))

    # Kitchen
    kitchen = Room('kitchen', 420, 520, description="The Kitchen")
    area.put_room(kitchen, (340, 460))

    # Study
    study = Room('study', 520, 320, description="The Study")
    area.put_room(study, (1240, 580))

    # Diningroom
    diningroom = Room('diningroom', 440, 740, description="The Dining Room")
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


    area.put_room(diningroom, (780, 60))

    # Pantry
    pantry = Room('pantry', 420, 380, description="The Pantry")
    area.put_room(pantry, (340, 60))

    # Billiardroom
    billiardroom = Room('billiardroom', 500, 360, description="The Billiard Room")
    area.put_room(billiardroom, (1240, 200))


    #area.create_door(foyer, cloakroom, (820, 1580), (800, 1580))
    #area.create_door(foyer, trophyroom, (1240, 1580), (1260, 1580))
    area.create_door(foyer, hall, (1040, 1480), (1040, 1460))
    area.create_door(hall, diningroom, (1040, 820), (1040, 800))
    area.create_door(hall, library, (1120, 1080), (1140, 1080))
    area.create_door(hall, lounge, (940, 1240), (920, 1240))
    #area.create_door(lounge, kitchen, (520, 1000), (520, 980))
    #area.create_door(diningroom, kitchen, (780, 600), (760, 600))
    #area.create_door(kitchen, pantry, (460, 460), (460, 440))
    #area.create_door(study, diningroom, (1240, 680), (1220, 680))
    #area.create_door(study, billiardroom, (1600, 580), (1600, 560))
    #area.create_door(library, study, (1420, 920), (1420, 900))

    area.entry_point_room_id = "foyer"

    create_npc(area, "butler", "butler", "butler_script", 'foyer')
    create_npc(area, "thomas", "dilettante", "thomas_script", 'lounge')
    create_npc(area, "anthony", "dilettante", "anthony_script", 'lounge')
    create_npc(area, "doctor", "major", "doctor_script", 'hall')
    create_npc(area, "barnes", "professor", "barnes_script", 'library')
    create_npc(area, "lizzy", "aunt", "lizzy_script", 'lounge')
    create_npc(area, "celia", "aunt", "celia_script", 'diningroom')

    create_npc(area, "bobby", "investigator", "bobby_script", 'hall')
    create_npc(area, "sergeant", "investigator", "sergeant_script", 'lounge')

    create_item(area, "clue", "foyer")

    container.save_area(area)

    game.area_map['first_floor'] = area.area_id
    game.start_areas = ['first_floor']

    container.save_game(game)

    return game

if __name__ == "__main__":
    create_game(None)
