
from actor import Actor

class NpcActor(Actor):
    def __init__(self, player_id = None, x = 0, y = 0):
        super(NpcActor, self).__init__(player_id, x, y)
