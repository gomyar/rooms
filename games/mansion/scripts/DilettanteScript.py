
import random

from script import *
import random


def kickoff(npc):
    wander(npc)

def wander(npc):
    while True:
        room_x, room_y = npc.room.position
        x = random.randint(room_x, room_x + npc.room.width)
        y = random.randint(room_y, room_y + npc.room.height)
        npc.walk_to(x, y)
        npc.sleep(random.randint(2, 4))

@expose
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
