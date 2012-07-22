
from room import Room


class RoomContainer(object):
    def __init__(self):
        self._rooms = dict()
        self._room_map = dict()

    def load_room(self, room_id):
        pass

    def save_room(self, room_id, room):
        pass

    def __getitem__(self, room_id):
        if room_id not in self._rooms:
            self._rooms[room_id] = self.load_room(self._room_map[room_id])
        return self._rooms[room_id]

    def __setitem__(self, room_id, room):
        db_id = self.save_room(room_id, room)
        self._room_map[room_id] = db_id
        self._rooms[room_id] = room
