
from character_actor import CharacterActor
from actor import expose
from actor import command


class NpcActor(CharacterActor):
    def __init__(self, actor_id):
        super(NpcActor, self).__init__(actor_id)
        self.model_type = actor_id

    def external(self):
        ex = super(NpcActor, self).external()
        ex['model_type'] = self.model_type
        return ex

    @command()
    def walk_to(self, x, y):
        x, y = float(x), float(y)
        path = self.room.get_path((self.x(), self.y()), (x, y))
        if not path or len(path) < 2:
            raise Exception("Wrong path: %s" % (path,))
        self.set_path(path)

    @expose()
    def chat(self, actor):
        actor.add_chat_message("Hi from %s", self.actor_id)

    @command()
    def exit(self, door_id):
        self.room.exit_through_door(self, door_id)
        self.instance.send_sync(self.actor_id)
