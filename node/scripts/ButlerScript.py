
import random

from scriptutils import *


class Reply:
    def __init__(self, text, interaction):
        self.text = text
        self.interaction = interaction

class Interaction:
    def do_something(self):
        pass

class Chat(Interaction):
    def __init__(self, text, replies=[]):
        self.text = text
        self.replies = replies
        for r in self.replies:
            r.parent = self

    def do_something(self):
        # do more chat
        pass

class Call(Interaction):
    def do_something(self):
        # call a method on the npc or something
        pass


class ButlerScript(Script):
    def kickoff(self):
        self.npc.set_state("greeting_guests")

    def state_greeting_guests(self):
        while True:
            self.walk_to(930, 1740)
            self.walk_to(935, 1740)
            self.walk_to(1180, 1740)
            self.walk_to(1180, 1590)
            self.walk_to(930, 1590)

    def event_player_moved_nearby(self, player_actor):
        self.start_chat(player_actor, self.chat_greet_guest)
        player_actor.add_chat_message("Good evening, Sir")

    def chat_greet_guest(self, player_chat=None):
        if not player_chat:
            return dict(
                text="Good evening, Sir",
                replies=[
                    'Nice house ya got here',
                    'Have all the guests arrived'
                ]
            )
        else:
            return dict(text="Indeed, Sir", replies=[])

def chat(text, replies=[]):
    return Chat(text, replies)
