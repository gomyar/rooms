
from rooms.player import Player


class Node(object):
    def __init__(self, host, port, container):
        self.host = host
        self.port = port
        self.container = container
        self.rooms = dict()
        self.players = dict()

    def manage_room(self, game_id, room_id):
        # load the room
        room = self.container.load_room(game_id, room_id)
        self.rooms[game_id, room_id] = room
        # load any players/playeractors currently in this room
        # kickoff the room
        pass

    def player_joins(self, username, game_id, room_id):
        # load player
        player = Player(username, game_id, room_id)
        self.players[username, game_id] = player
        player.token = self._create_token()
        # add player to room
        # call player_created() script?
        # return token
        return "TOKEN1"
