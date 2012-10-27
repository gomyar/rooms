
from actor import Actor
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
            player.say(message)
            player.add_log("You say: %s" % (message,))
        response = script.said(message)
        if response:
            self.say(response)
            player.add_log("%s says: %s" % (self.actor_id, response))
        self.stop()
        self._delayed_chat_response()
        if not script.choice_list():
            self.chat_scripts.pop(player.actor_id)
            return dict(command="end_chat", actor_id=self.actor_id)
        else:
            return dict(command="chat", actor_id=self.actor_id,
                msg=response, choices=script.choice_list())

    def _delayed_chat_response(self):
        self._queue_script_method("chat_delay", self, [], {})

    def load_chat(self, chat_id):
        return load_chat_script(chat_id, self.script, self)
