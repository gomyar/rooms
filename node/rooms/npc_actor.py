
import eventlet

from character_actor import CharacterActor
from actor import expose
import scriptutils

import logging
log = logging.getLogger("rooms.npc")


class NpcActor(CharacterActor):
    def __init__(self, actor_id, script=None):
        super(NpcActor, self).__init__(actor_id)
        self.model_type = actor_id
        if script:
            self.script = script
        self.speed = 90.0
        self.previous_state = None
        self.chat_scripts = dict()
        self.gthread = None

    def set_state(self, state):
        super(NpcActor, self).set_state(state)
        callback_method = "state_%s" % (state,)
        if self.gthread:
            try:
                self.gthread.kill()
            except:
                pass
        if hasattr(self.script, callback_method):
            state_changed = getattr(self.script, callback_method)
            log.debug("NPC %s running %s", self.actor_id, state_changed)
            self.gthread = eventlet.spawn(state_changed, self)

    @expose()
    def chat(self, player, message=""):
        if self.state != "chatting":
            self.previous_state = self.state
            self.chat_scripts[player.actor_id] = self.script.chat(player)
        self.set_state("chatting")
        script = self.chat_scripts[player.actor_id]
        if message:
            player.add_chat_message("You say : %s", message)
        response = script.said(message)
        if response:
            player.add_chat_message("%s says: %s", self.actor_id, response)
        if not script.choice_list():
            self.chat_scripts.pop(player.actor_id)
            self.set_state(self.previous_state)
            return dict(command="end_chat", actor_id=self.actor_id)
        else:
            return dict(command="chat", actor_id=self.actor_id,
                msg=response, choices=script.choice_list())

    def event(self, event_id, *args, **kwargs):
        event_method = "event_%s" % (event_id,)
        if hasattr(self.script, event_method):
            getattr(self.script, event_method)(*args, **kwargs)

    def load_script(self, script_class):
        script = scriptutils.load_script(script_class)
        script.npc = self
        self.script = script

    def kickoff(self):
        self.script.kickoff(self)
