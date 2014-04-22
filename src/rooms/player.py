
class Player(object):
    def __init__(self, username, game_id):
        self.username = username
        self.game_id = game_id

    def __repr__(self):
        return "<Player %s in game %s>" % (self.username, self.game_id)

    def __eq__(self, rhs):
        return rhs and type(rhs) is Player and \
            self.username == rhs.username and self.game_id == rhs.game_id
