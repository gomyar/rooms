
import json


def jsonview(obj):
    return JsonView.get_instance().view(obj)

class JsonView(object):
    _instance = None

    def __init__(self):
        self.views = dict(
            Actor=self.view_actor,
            State=self.view_state,
            Vector=self.view_vector,
            Position=self.view_position,
        )

    @staticmethod
    def get_instance():
        if not JsonView._instance:
            JsonView._instance = JsonView()
        return JsonView._instance

    def view(self, obj):
        return json.loads(json.dumps(obj, default=self._encode))

    def _encode(self, obj):
        obj_name =  type(obj).__name__
        if obj_name in self.views:
            return self.views[obj_name](obj)
        raise TypeError("Cannot serialize object %s" % obj_name)

    def view_actor(self, actor):
        return dict(
            actor_id=actor.actor_id,
            state=actor.state,
            vector=actor.vector,
            actor_type=actor.actor_type,
            username=actor.player_username,
        )

    def view_state(self, state):
        return dict(state)

    def view_vector(self, vector):
        return dict(start_pos=vector.start_pos, start_time=vector.start_time,
            end_pos=vector.end_pos, end_time=vector.end_time)

    def view_position(self, position):
        return dict(x=position.x, y=position.y, z=position.z)
