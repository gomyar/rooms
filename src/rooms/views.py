
import json


def jsonview(obj):
    return JsonView.get_instance().view(obj)

class JsonView(object):
    _instance = None

    def __init__(self):
        self.views = dict(
            Actor=self.view_actor,
            State=self.view_state,
        )

    @staticmethod
    def get_instance():
        if not JsonView._instance:
            JsonView._instance = JsonView()
        return JsonView._instance

    def view(self, obj):
        return json.dumps(obj, default=self._encode, indent=4)

    def _encode(self, obj):
        obj_name =  type(obj).__name__
        if obj_name in self.views:
            return self.views[obj_name](obj)
        raise TypeError("Cannot serialize object %s" % obj_name)

    def view_actor(self, actor):
        return dict(
            actor_id=actor.actor_id,
            state=actor.state,
        )

    def view_state(self, state):
        return dict(state)
