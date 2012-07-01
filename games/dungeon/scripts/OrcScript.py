
import random

from script import *


class OrcScript(Script):
    def kickoff(self):
        self.set_state("hunting")

    def state_hunting(self):
        while True:
            self.walk_to_nearest_player()
#            self.attack_nearest_player()
