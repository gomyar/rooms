

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
        room_data = self.container.dbase.find_and_modify(
            'rooms',
            query={'active': False, 'requested': True, '__type__': 'Room'},
            update={
                '$set':{'active': True, 'requested': False, 'node': self.name},
                '$setOnInsert':{'active': False,'node_name': None},
            },
            new=True,
        )
        room = self.container._decode_enc_dict(room_data)
        self.rooms[room.game_id, room.room_id] = room

    def player_connects(self, username, game_id):
        pass
