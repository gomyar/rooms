
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
        end_time = self.npc.path_end_time()
        self.sleep(end_time - time.time())

    def state_chatting(self):
        print "Chatting...."
        self.npc.stop_walking()
        self.sleep(10)
        print "Waking up..."
        self.npc.set_state(self.npc.previous_state)


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

    def choice_list(self):
        return [str(choice.query_text) for choice in self.choices]


def chat(query_text, response, choices=[]):
    c = Chat(query_text, response, choices)
    for choice in choices:
        choice.parent = c
    return c
