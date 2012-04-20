
from actor import Actor
from actor import expose

class Bed(Actor):
    def __init__(self, object_id, x = 0, y = 0):
        super(Bed, self).__init__(object_id, x, y)

    @expose
    def sleep_in(self, player):
        player.state = "sleeping"
        player.set_position(self.x(), self.y())
        self.state = "slept_in"

    @expose
    def get_out(self, player):
        player.state = "idle"
        self.state = "idle"
