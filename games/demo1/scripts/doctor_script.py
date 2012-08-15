
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

def hold_it(npc):
    npc.talk()
    
@conversation
def chat(npc, player):
    conv = create_chat(
        c("Excuse me I...", "Quickly!! He's gone mad! Someone needs to calm him down before he does some harm."),
        c("Hold it", hold_it),
    )
    return conv
