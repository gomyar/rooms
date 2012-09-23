
from script import *


def kickoff(npc):
#    walk_around_clockwise(npc)
    move_to_object(npc, "t1")
    npc.say("I am at t1")
    npc.sleep(3)
    move_to_object(npc, "t2")
    npc.say("I am at t2")
    npc.sleep(3)

    
def walk_around_clockwise(npc):
    npc.move_to(930, 1740)
    npc.sleep(5)
    npc.move_to(1180, 1740)
    npc.sleep(5)
    npc.move_to(1180, 1590)
    npc.sleep(5)
    npc.move_to(930, 1590)
    npc.sleep(5)

def walk_around_anticlockwise(npc):
    npc.move_to(930, 1590)
    npc.sleep(5)
  
    npc.move_to(1180, 1590)
    npc.sleep(5)

    npc.move_to(1180, 1740)
    npc.sleep(5)

    npc.move_to(930, 1740)
    npc.sleep(5)
    
def give_evidence_means(npc, player):
    player.add_evidence("means", "The butler is a "
        "former army sergeant with hand to hand combat training")

def give_evidence_motive(npc, player):
    player.add_evidence("motive", "The butler was about to "
        "be fired from his job")

def give_evidence_opportunity(npc, player):
    player.add_evidence("opportunity", "The butler was "
        "in the study at the time of the murder")


@expose
def walk_clockwise(npc, player):
    npc.state.clockwise = True

@expose
def walk_anticlockwise(npc, player):
    npc.state.clockwise = False
    
    
@conversation
def chat(npc, player):
    conv = npc.load_chat("butler_talk")
    return conv
