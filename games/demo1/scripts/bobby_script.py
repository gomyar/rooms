
from script import *


def kickoff():
    arranging_dining_room()

def arranging_dining_room():
    npc.move_to(800, 220)
    npc.sleep(10)
    npc.move_to(880, 520)
    npc.sleep(5)
    npc.move_to(880, 440)
    npc.sleep(5)
    npc.move_to(880, 360)
    npc.sleep(5)
    npc.move_to(870, 150)
    npc.sleep(5)
    npc.move_to(1160, 100)
    npc.sleep(5)

def learn_about_jezabel(player):
    player.add_chat_message("Oh, shes just upset about the murder. "
        "Try asking her about her season in Paris")
    player.state.jezabel_ask_about_paris = True

@conversation
def chat(player):
    conv = create_chat(
        c("Excuse me madame", "Yes, Good evening.",
            c("When will dinner be ready?", "When cook says so.",
                c("Whats holding up the cook?",
                    "Well, she's a perfectionist you see."),
                c("Could I grab something from the kitchen?",
                    "Certainly not, it will ruin your apetite, you'll "
                    "insult Cook."),
            ),
        )
    )
    if player.state.jezabel_is_defensive:
        conv.add(c("What's wrong with Jezabel, she seems excitable",
            call(npc.learn_about_jezabel, player),
            ))
    return conv
