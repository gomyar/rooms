
from character_actor import CharacterActor
from actor import expose
from actor import command


class NpcActor(CharacterActor):
    def __init__(self, actor_id, npc_script=None):
        super(NpcActor, self).__init__(actor_id)
        self.model_type = actor_id
        self.npc_script = npc_script
        self.speed = 90.0

    def set_state(self, state):
        super(NpcActor, self).set_state(state)
        callback_method = "state_%s" % (state,)
        if hasattr(self.npc_script, callback_method):
            state_changed = getattr(self.npc_script, callback_method)
            state_changed()

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
        self.send_to_players_in_room("actor_update", **self.external())

    def load_script(self, script_class):
        module = __import__("scripts.%s" % (script_class,),
            fromlist=['scripts'])
        script = getattr(module, script_class)()
        script.npc = self
        self.npc_script = script

    def kickoff(self):
        self.npc_script.kickoff()

    @expose()
    def chat(self, actor):
        actor.add_chat_message("Hi from %s", self.actor_id)
