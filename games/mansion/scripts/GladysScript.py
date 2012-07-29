
from script import *


def kickoff(npc):
    arranging_dining_room(npc)

def state_arranging_dining_room(npc):
    while True:
        npc.walk_to(800, 220)
        npc.sleep(10)
        npc.walk_to(880, 520)
        npc.sleep(5)
        npc.walk_to(880, 440)
        npc.sleep(5)
        npc.walk_to(880, 360)
        npc.sleep(5)
        npc.walk_to(870, 150)
        npc.sleep(5)
        npc.walk_to(1160, 100)
        npc.sleep(5)

def learn_about_jezabel(npc, player):
    player.add_chat_message("Oh, shes just upset about the murder. "
        "Try asking her about her season in Paris")
    player.data['jezabel_ask_about_paris'] = True

def chat(npc, player):
    conv = chat(
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
    if player.data.get('jezabel_is_defensive'):
        conv.add(c("What's wrong with Jezabel, she seems excitable",
            call(npc.learn_about_jezabel, player),
            ))
    return conv
