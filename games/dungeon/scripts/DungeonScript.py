
from scriptutils import load_script
from script import *

from room import Room


class DungeonScript(Script):
    def _create_room(self, area, x, y, from_room):
        room_id = "%s,%s" % (x, y)
        room = Room(room_id, (x * 400, y * 400), 390, 390,
            description=room_id)
        area.rooms[room.room_id] = room
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
