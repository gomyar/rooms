
import random

from script import *


def kickoff():
    random_wander()

def random_wander():
    room_x, room_y = npc.room.position
    x = random.randint(room_x, room_x + npc.room.width)
    y = random.randint(room_y, room_y + npc.room.height)
    npc.move_to(x, y)
    npc.sleep(random.randint(2, 4))

def hold_it():
    npc.talk()
    
@conversation
def chat(player):
    return npc.load_chat("doctor_talk")
