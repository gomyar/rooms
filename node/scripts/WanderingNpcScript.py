
from scriptutils import *
import random

class WanderingNpcScript(Script):
    def kickoff(self):
        while True:
            pos = self.random_position()
            print "%s Walking to %s" % (self.npc.actor_id, pos,)
            self.npc.walk_to(*pos)

            self.sleep(random.randint(3, 6))
