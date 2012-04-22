
from actor import Actor
from actor import expose
from actor import command


class PlayerActor(Actor):
    def __init__(self, player_id = None, position=(0, 0)):
        super(PlayerActor, self).__init__(player_id, position)

    @command()
    def walk_to(self, x, y):
        x, y = float(x), float(y)
        self.set_path([ (self.x(), self.y()), (x, y) ])

    @expose()
    def chat(self, actor):
        actor.add_chat_message("Hi from %s", self.actor_id)
