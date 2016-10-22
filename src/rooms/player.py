
from rooms.actor import Actor


class PlayerActor(Actor):
    def __init__(self, *args, **kwargs):
        super(PlayerActor, self).__init__(*args, **kwargs)
        self.status = None
        self.token = None
        self.timeout_time = None

    @property
    def is_player(self):
        return True

    def __repr__(self):
        return "<PlayerActor %s in game %s room %s>" % (self.username,
            self.game_id, self.room_id)

    def remove(self):
        raise Exception("Removing PlayerActors not allowed")
