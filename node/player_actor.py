
from actor import Actor
from actor import expose


class PlayerActor(Actor):
    def __init__(self, player_id = None, x = 0, y = 0):
        super(PlayerActor, self).__init__(player_id, x, y)

    @expose
    def walk_to(self, x, y):
        x, y = float(x), float(y)
        self.set_path([ (self.x(), self.y()), (x, y) ])

    @expose
    def commands(self):
        return [
            { 'name': 'Sleep' },
        ]
