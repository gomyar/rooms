
from room import Room


class RoomContainer(object):
    def __init__(self, area, container):
        self._area = area
        self._container = container
        self._rooms = dict()
        self._room_map = dict()

    def load_room(self, room_id):
        return self._container.load_room(room_id)

    def save_room(self, room_id, room):
        return self._container.save_room(room)

    def values(self):
        return self._rooms.values()

    def pop(self, room_id):
        self._rooms.pop(room_id)

    def __iter__(self):
        for room_id in self._rooms:
            yield room_id

    def __getitem__(self, room_id):
        if room_id not in self._rooms:
            room = self.load_room(self._room_map[room_id])
            self._rooms[room_id] = room
            self._rooms[room_id].area = self._area
            for actor in room.actors.values():
                actor.kick()
        return self._rooms[room_id]

    def __setitem__(self, room_id, room):
        db_id = self.save_room(room_id, room)
        self._room_map[room_id] = db_id
        self._rooms[room_id] = room
