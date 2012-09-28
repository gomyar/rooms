

from script import *


def kickoff(npc):
    npc.move_to(1100, 1100)
    npc.say("Worst case I've ever seen...")
    npc.sleep(5)
    npc.move_to(1000, 1000)
    npc.sleep(6)
    npc.say("Perhaps a sleeping pill")
    npc.sleep(3)
    npc.say("No... he'll never take one")
    npc.sleep(3)

    
@conversation
def chat(npc, player):
    return npc.load_chat("doctor_talk")
