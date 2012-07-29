
import random

from script import *


def kickoff(npc):
    pottering_around_lounge(npc)

def state_pottering_around_lounge(npc):
    while True:
        npc.walk_to(830, 620)
        npc.sleep(2)
        npc.walk_to(860, 460)
        npc.sleep(3)
        npc.walk_to(850, 690)
        npc.sleep(2)
        npc.walk_to(1170, 690)
        npc.sleep(3)
        npc.walk_to(1030, 720)
        npc.sleep(5)

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
