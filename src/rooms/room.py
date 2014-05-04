
from rooms.position import Position
from rooms.actor import Actor


class State(dict):
    def __init__(self, actor):
        super(State, self).__init__()
        self.__dict__['actor'] = actor

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value
        # might need to check the value has actually changed before update
        # actually, we had a diff/cache idea for that didn't we?
        self.actor.send_actor_update()


class Room(object):
    def __init__(self, game_id, room_id, topleft, bottomright):
        self.game_id = game_id
        self.room_id = room_id
        self.topleft = topleft
        self.bottomright = bottomright

    @property
    def width(self):
        return self.bottomright.x - self.topleft.x

    @property
    def height(self):
        return self.bottomright.y - self.topleft.y

    @property
    def center(self):
        return Position(
            self.topleft.x + (self.bottomright.x - self.topleft.x) / 2,
            self.topleft.y + (self.bottomright.y - self.topleft.y) / 2,
            self.topleft.z + (self.bottomright.z - self.topleft.z) / 2,
        )

    def kick(self):
        pass

    def create_actor(self, script_name):
        actor = Actor()
        actor.room = self
        actor.script.load_script(script_name)
        actor.script.call("created", actor)
        actor.kick()
        return actor
