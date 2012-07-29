
import random

from script import *


def kickoff(npc):
    random_wander(npc)

def random_wander(npc):
    room_x, room_y = npc.room.position
    x = random.randint(room_x, room_x + npc.room.width)
    y = random.randint(room_y, room_y + npc.room.height)
    npc.move_to(x, y)
    npc.sleep(random.randint(2, 4))

def chat(npc, player):
    conv = chat(
        c("Excuse me Sir", "Yes, thank you, mines a brandy"),
        c("Where were you at the time of the murder?",
            "Yes, it's a little chilly, throw another log in the "
            "fireplace there's a good boy"),
    )
    return conv
