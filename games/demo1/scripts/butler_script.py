
from script import *


def kickoff(npc):
    npc.move_to(900, 1600)
    npc.sleep(15)
    npc.say("Can I get you anything sir?")
    
    
@conversation
def chat(npc, player):
#    conv = npc.load_chat("butler_talk")
    conv = npc.load_chat("bobby_angry")
    return conv
