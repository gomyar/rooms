
import eventlet

from character_actor import CharacterActor
from actor import expose
import scriptutils


class NpcActor(CharacterActor):
    def __init__(self, actor_id, npc_script=None):
        super(NpcActor, self).__init__(actor_id)
        self.model_type = actor_id
        if npc_script:
            self.npc_script = npc_script
            self.npc_script.npc = self
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
        if hasattr(self.npc_script, callback_method):
            state_changed = getattr(self.npc_script, callback_method)
            self.gthread = eventlet.spawn(state_changed)

    @expose()
    def chat(self, player, message=""):
        if self.state != "chatting":
            self.previous_state = self.state
            self.chat_scripts[player.actor_id] = self.npc_script.chat(player)
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
        if hasattr(self.npc_script, event_method):
            getattr(self.npc_script, event_method)(*args, **kwargs)

    def external(self):
        ex = super(NpcActor, self).external()
        ex['model_type'] = self.model_type
        return ex

    def walk_to(self, x, y):
        x, y = float(x), float(y)
        path = self.room.get_path((self.x(), self.y()), (x, y))
        if not path or len(path) < 2:
            raise Exception("Wrong path: %s" % (path,))
        self.set_path(path)
        self.send_actor_update()

    def path_end_time(self):
        return self.path[-1][2]

    def load_script(self, script_class):
        script = scriptutils.load_script(script_class)
        script.npc = self
        self.npc_script = script

    def kickoff(self):
        self.npc_script.kickoff()
