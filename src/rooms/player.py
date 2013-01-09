
class Player(object):
    def __init__(self, username):
        self.username = username
        self.game_id = None
        self.area_id = None
        self.room_id = None
        self.actor_id = None
        self.state = dict()

    def __repr__(self):
        return "<Player %s>" % (self.username,)
