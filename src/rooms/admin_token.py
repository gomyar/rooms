

class AdminToken(object):
    def __init__(self, token, game_id, room_id, timeout_time):
        self.token = token
        self.game_id = game_id
        self.room_id = room_id
        self.timeout_time = timeout_time
