
from script import *


def kickoff(npc):
    npc.move_to(900, 1600)
    npc.sleep(15)
    npc.say("Can I get you anything sir?")
    
    
@conversation
def chat(npc, player):
    conv = npc.load_chat("butler_talk")
    conv.add_chat(npc.load_chat("butler_talk_2"))
    return conv

def walk_to_cloakroom(npc):
    npc.say("Of course sir")
    npc.move_to(1300, 1600)
    npc.say("Trenchcoat was it sir?")
    npc.sleep(2)
    