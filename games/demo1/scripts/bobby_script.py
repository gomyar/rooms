
from rooms.script import *


def kickoff(npc):
    npc.move_to(1100, 1150)

    
@conversation
def chat(npc, player):
    conv = npc.load_chat("bobby_talk")
    return conv