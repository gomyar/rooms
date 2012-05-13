
import random
import time

import eventlet


class Script:
    def room(self):
        return self.npc.room

    def random_position(self):
        room = self.room()
        return (
            random.randint(room.position[0],
            room.position[0] + room.width),
            random.randint(room.position[1],
            room.position[1] + room.height)
        )

    def sleep(self, seconds):
        eventlet.sleep(seconds)

    def walk_to(self, x, y):
        self.npc.walk_to(x, y)
        end_time = self.npc.path[-1][2]
        self.sleep(end_time - time.time())
