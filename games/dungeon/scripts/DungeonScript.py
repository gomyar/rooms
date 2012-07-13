
import uuid

from scriptutils import load_script
from script import *

from room import Room

from npc_actor import NpcActor
import OrcScript
import player_script


class DungeonScript(Script):
    def _create_room(self, area, x, y, from_room):
        room_id = "%s,%s" % (x, y)
        room = Room(room_id, (x * 400, y * 400), 390, 390,
            description=room_id)
        area.add_room(room)
        area.create_door(room, from_room)
        return room

    def kickoff(self, area):
        room1 = self._create_room(area, 0, 1, area.rooms['entrance'])
        room2 = self._create_room(area, 0, 2, room1)
        room3 = self._create_room(area, 0, 3, room2)

        room4 = self._create_room(area, 0, -1, area.rooms['entrance'])
        room5 = self._create_room(area, 0, -2, room4)
        room6 = self._create_room(area, 0, -3, room5)

        room7 = self._create_room(area, 1, 0, area.rooms['entrance'])
        room8 = self._create_room(area, 2, 0, room7)
        room9 = self._create_room(area, 3, 0, room8)

        room10 = self._create_room(area, -1, 0, area.rooms['entrance'])
        room11 = self._create_room(area, -2, 0, room10)
        room12 = self._create_room(area, -3, 0, room11)

    def player_joined_instance(self, player):
        player.script = player_script
        player.stats['hp'] = 10

    def player_enters_room(self, room, player):
        orc = NpcActor(str(uuid.uuid1()), OrcScript)
        orc.model_type = "orc"
        room.add_npc(orc, room.center())
        orc.kickoff()
