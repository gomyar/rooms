
from rooms.actor import Actor


class PlayerActor(Actor):
    def __init__(self, room, actor_type, script, username, actor_id=None,
            game_id=None, room_id=None):
        super(PlayerActor, self).__init__(room, actor_type, script,
            username=username, actor_id=actor_id, game_id=game_id,
            room_id=room_id)
        self.is_player = True

    def __repr__(self):
        return "<PlayerActor %s in game %s room %s>" % (self.username,
            self.game_id, self.room_id)

#    def __eq__(self, rhs):
#        return rhs and type(rhs) is PlayerActor and \
#            super(PlayerActor, self).__eq__(rhs)
