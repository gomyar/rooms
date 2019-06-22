
import json


def jsonview(obj):
    return JsonView.get_instance().view(obj)

class JsonView(object):
    _instance = None

    def __init__(self):
        self.views = dict(
            Actor=self.view_actor,
            PlayerActor=self.view_actor,
            State=self.view_state,
            Vector=self.view_vector,
            Position=self.view_position,
            Game=self.view_game,
            SyncDict=self.view_syncdict,
            SyncList=self.view_synclist,
            Item=self.view_item,
            OnlineNode=self.view_onlinenode,
            Room=self.view_room,
        )

    @staticmethod
    def get_instance():
        if not JsonView._instance:
            JsonView._instance = JsonView()
        return JsonView._instance

    def view(self, obj):
        return json.loads(self.dumps(obj))

    def dumps(self, obj):
        return json.dumps(obj, default=self._encode)

    def _encode(self, obj):
        obj_name =  type(obj).__name__
        if obj_name in self.views:
            return self.views[obj_name](obj)
        raise TypeError("Cannot serialize object %s" % obj_name)

    def view_actor(self, actor):
        return dict(
            actor_id=actor.actor_id,
            parent_id=actor.parent_id,
            game_id=actor.game_id,
            state=actor.state,
            path=actor.path,
            speed=actor.speed,
            actor_type=actor.actor_type,
            username=actor.username,
            docked_with=actor.docked_with.actor_id if \
                actor.docked_with else None,
            visible=actor.visible,
            script=actor.script.script_name if actor.script else "",
            exception=actor._exception,
        )

    def view_state(self, state):
        return dict(state)

    def view_vector(self, vector):
        return dict(start_pos=vector.start_pos, start_time=vector.start_time,
            end_pos=vector.end_pos, end_time=vector.end_time)

    def view_position(self, position):
        return dict(x=position.x, y=position.y, z=position.z)

    def view_game(self, game):
        return dict(game_id=str(game._id), owner_id=game.owner_id,
                    state=game.state)

    def view_syncdict(self, syncdict):
        return syncdict._data

    def view_synclist(self, synclist):
        return synclist._data

    def view_item(self, item):
        return dict(category=item.category, item_type=item.item_type,
            data=item.data)

    def view_onlinenode(self, onlinenode):
        return dict(name=onlinenode.name, host=onlinenode.host,
            load=onlinenode.load, uptime=onlinenode.uptime)

    def view_room(self, room):
        return dict(game_id=room.game_id, room_id=room.room_id)
