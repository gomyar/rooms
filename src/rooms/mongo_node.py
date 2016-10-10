

from rooms.actor import Actor


ROOM_LOAD_STATES = ['inactive', 'pending', 'active', 'deactivating']
# Load states:
#   active: room is currently running on a node
#       active = True, pending = N/A, deactivating = False
#   inactive: room is not running on a node nor is it needed
#       active = False, pending = False, deactivating = False
#   pending: room is not running but has been requested
#       active = False, pending = True, deactivating = False
#   deactivating: room is running, has not been requested, is being shut down
#       active = True, pending = N/A, deactivating = True


class Room(object):
    def __init__(self, game_id, room_id):
        self.game_id = game_id
        self.room_id = room_id

        self.active_state = True
        self.pending_state = True
        self.deactivating_state = False


class Player(Actor):
    pass


class Node(object):
    def __init__(self, container, name):
        self.container = container
        self.name = name
        self.rooms = dict()

    def load_next_pending_room(self):
        room = self.container.load_next_pending_room(self.name)
        if room:
            self.rooms[room.game_id, room.room_id] = room

    def player_connects(self, username, game_id):
        pass
