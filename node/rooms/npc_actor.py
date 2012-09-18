
import eventlet

from actor import Actor
from script import expose
from rooms.chat import load_chat as load_chat_script

import logging
log = logging.getLogger("rooms.npc")


class NpcActor(Actor):
    def __init__(self, actor_id):
        super(NpcActor, self).__init__(actor_id)
        self.model_type = actor_id
        self.speed = 90.0
        self.chat_scripts = dict()
        self.gthread = None

    def create_chat(self, player, conversation):
        self.chat_scripts[player.actor_id] = conversation

    def chat(self, player, message=""):
        script = self.chat_scripts[player.actor_id]
        if message:
            player.add_chat_message("You say : %s", message)
        response = script.said(message)
        if response:
            player.add_chat_message("%s says: %s", self.actor_id, response)
        if not script.choice_list():
            self.chat_scripts.pop(player.actor_id)
            return dict(command="end_chat", actor_id=self.actor_id)
        else:
            return dict(command="chat", actor_id=self.actor_id,
                msg=response, choices=script.choice_list())

    def load_chat(self, chat_id):
        return load_chat_script(chat_id, self.script)
