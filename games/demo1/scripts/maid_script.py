
import random

from rooms.script import *


def kickoff(npc):
    pottering_around_lounge(npc)

def pottering_around_lounge(npc):
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
def chat(npc, player):
    conv = chat(
        c("Excuse me madame", "What? Yes, what? Speak up Deary...",
            c("How can I find the Dining Room?",
                "Sorry Deary, you'll have to speak up..."),
            c("How are you feeling?",
                "Sorry Deary, you'll have to speak up..."),
            c("Where were you at the time of the murder?",
                "Sorry Deary, you'll have to speak up..."),
        )
    )
    return conv
