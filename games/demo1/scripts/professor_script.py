
import random

from script import *


def kickoff(npc):
    pottering_around_library(npc)

def pottering_around_library(npc):
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

def chat(npc, player):
    conv = chat(
        c("Hello...", "Marty, quick we have to get you.., oh, never mind.",
            c("What did you just say?",
                "Nothing, what can I do for you?"),
            c("Yes I'm looking for Doctor Willow",
                "I don't know where he is, I have very important work to "
                "do here, the experiment is in a critical state..."),
            c("What's that in the beaker?",
                "Please don't touch that, very volatile, it's at a "
                "critical stage."),
        )
    )
    return conv
