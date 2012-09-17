
import random

from script import *


def kickoff():
    pottering_around_library()

def pottering_around_library():
    npc.move_to(830, 620)
    npc.sleep(2)
    npc.move_to(860, 460)
    npc.sleep(3)
    npc.move_to(850, 690)
    npc.sleep(2)
    npc.move_to(1170, 690)
    npc.sleep(3)
    npc.move_to(1030, 720)
    npc.sleep(5)

@conversation
def chat(player):
    return npc.load_chat("professor_talk")
