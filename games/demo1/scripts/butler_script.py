
from script import *


def kickoff(npc):
    npc.move_to(900, 1600)
    npc.sleep(15)
    npc.say("Can I get you anything sir?")
    
    
@conversation
def chat(npc, player):
    conv = npc.load_chat("butler_talk")
    return conv

def walk_to_cloakroom(npc):
    npc.say("I am walking to the cloakroom now")