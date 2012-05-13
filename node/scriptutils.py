
import random
import time

import eventlet


class Script:
    def room(self):
        return self.npc.room

    def random_position(self):
        room = self.room()
        return (
            random.randint(room.position[0],
            room.position[0] + room.width),
            random.randint(room.position[1],
            room.position[1] + room.height)
        )

    def sleep(self, seconds):
        eventlet.sleep(seconds)

    def walk_to(self, x, y):
        self.npc.walk_to(x, y)
        end_time = self.npc.path[-1][2]
        self.sleep(end_time - time.time())

    def start_chat(self, actor, chat):
        actor.set_state("chatting")
        actor.interacting_with = self.npc

        self.npc.previous_state = self.npc.state
        self.npc.set_state("chatting")
        self.npc.interacting_with = actor
        self.npc.chat_script = chat
        self.npc.current_chat = chat

        actor.add_chat_message(chat.query_text)
        actor.add_chat_message(chat.response)


class Chat:
    def __init__(self, query_text, response, choices=[]):
        self.query_text = query_text
        self.response = response
        self.choices = choices
        self.parent = None

    def said(self, message):
        for choice in self.choices:
            if choice.query_text == message:
                return choice
        raise Exception("Not understood")


def chat(query_text, response, choices=[]):
    c = Chat(query_text, response, choices)
    for choice in choices:
        choice.parent = c
    return c
