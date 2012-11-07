
from rooms.script import *


def kickoff(npc):
    npc.move_to(900, 1300)
    

@conversation
def chat(npc, player):
    conv = npc.load_chat("sergeant_talk")
    return conv