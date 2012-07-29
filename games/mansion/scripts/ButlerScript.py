
from script import *


def kickoff(npc):
    walk_around()

def walk_around(npc):
    while True:
        npc.move_to(930, 1740)
        npc.sleep(5)
        npc.move_to(1180, 1740)
        npc.sleep(5)
        npc.move_to(1180, 1590)
        npc.sleep(5)
        npc.move_to(930, 1590)
        npc.sleep(5)

def give_evidence_means(npc, player):
    player.add_evidence(npc, "means", "The butler is a "
        "former army sergeant with hand to hand combat training")

def give_evidence_motive(npc, player):
    player.add_evidence(npc, "motive", "The butler was about to "
        "be fired from his job")

def give_evidence_opportunity(npc, player):
    player.add_evidence(npc, "opportunity", "The butler was "
        "in the study at the time of the murder")

@expose()
def chat(npc, player):
    conv = chat(
        c("Hullo Jeeves", "Good evening, Sir",
            c("Have all the guests arrived yet?", "Not quite, Sir",
                c("When is dinner starting?", "Around 9, Sir"),
                c("Where is the owner?",
                    "Lady Pinkerton in in the dining room, Sir"),
            ),
            c("Yes, thank you Jeeves, any chance of a drink?",
                "The Lounge is straight ahead on the left, Sir")
        )
    )
    if not player.has_evidence(npc, "means"):
        conv.add(c("I see you've had some experience in combat...",
            call(npc.give_evidence_means, player)))
    if not player.has_evidence(npc, "motive"):
        conv.add(c("Why did you hate Doctor Killsworth?",
            call(npc.give_evidence_motive, player)))
    if not player.has_evidence(npc, "opportunity"):
        conv.add(c("Where were you at the time of the murder?",
            call(npc.give_evidence_opportunity, player)))
    return conv
