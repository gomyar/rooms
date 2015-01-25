
from rooms.actor import Actor


class PlayerActor(Actor):
    @property
    def is_player(self):
        return True

    def __repr__(self):
        return "<PlayerActor %s in game %s room %s>" % (self.username,
            self.game_id, self.room_id)
