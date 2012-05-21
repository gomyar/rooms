
import random
import time

import eventlet

from chat import Chat

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
        end_time = self.npc.path_end_time()
        self.sleep(end_time - time.time())

    def state_chatting(self):
        print "Chatting...."
        self.npc.stop_walking()
        self.sleep(10)
        print "Waking up..."
        self.npc.set_state(self.npc.previous_state)


