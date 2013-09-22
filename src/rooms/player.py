
class Player(object):
    def __init__(self, username, game_id):
        self.username = username
        self.game_id = game_id
        self.area_id = None
        self.room_id = None
        self.actor_id = None
        self.state = dict()

    def __repr__(self):
        return "<Player %s:%s>" % (self.username, self.game_id)
