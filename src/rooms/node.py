

class Node(object):
    def __init__(self, host, port, container):
        self.host = host
        self.port = port
        self.container = container

    def manage_room(self, game_id, room_id):
        # load the room
        # load any players/playeractors currently in this room
        # kickoff the room
        pass

    def connect_player(self, username, game_id, room_id):
        # load player
        # add player to room
        # call player_created() script?
        # return token
        pass
