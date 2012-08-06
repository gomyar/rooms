
import eventlet

from actor import Actor
from actor import expose

import logging
log = logging.getLogger("rooms.npc")


class NpcActor(Actor):
    def __init__(self, actor_id):
        super(NpcActor, self).__init__(actor_id)
        self.model_type = actor_id
        self.speed = 90.0
        self.previous_state = None
        self.chat_scripts = dict()
        self.gthread = None

    def process_command_queue(self):
        self.running = True
        try:
            while self.running:
                self.sleep(1)
                self.script.kickoff(self)
        except:
            log.exception("Exception running kickoff for %s", self.model_type)

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

    def kickoff(self):
        self.script.kickoff(self)
