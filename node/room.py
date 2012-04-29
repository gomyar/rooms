
from door import Door

from basicrect_geography import BasicRectGeography

geog = BasicRectGeography()

class RoomObject(object):
    def __init__(self, width, height, position=(0, 0)):
        self.width = width
        self.height = height
        self.position = position

    def __repr__(self):
        return "<RoomObject %s, %s, %s, %s>" % self.wall_positions()

    def external(self):
        return dict(width=self.width, height=self.height,
            position=self.position)

    def left(self):
        return self.position[0]

    def top(self):
        return self.position[1]

    def right(self):
        return self.position[0] + self.width

    def bottom(self):
        return self.position[1] + self.height

    def wall_positions(self):
        return (self.left(), self.top(), self.right(), self.bottom())


class Room(object):
    def __init__(self, room_id=None, position=(0, 0), width=50, height=50):
        self.room_id = room_id
        self.position = position
        self.width = width
        self.height = height
        self.map_objects = []
        self.actors = dict()

    def __eq__(self, rhs):
        return rhs and self.room_id == rhs.room_id

    def __repr__(self):
        return "<Room %s at %s w:%s h:%s>" % (self.room_id,self.position,
            self.width, self.height)

    def add_object(self, map_object, rel_position=(0, 0)):
        position = (self.position[0] + rel_position[0],
            self.position[1] + rel_position[1])
        map_object.position = position
        self.map_objects.append(map_object)

    def external(self):
        return dict(room_id=self.room_id, position=self.position,
            width=self.width, height=self.height,
            map_objects=[m.external() for m in self.map_objects],
            subdivided=[r.external() for r in geog.subdivide(self)])

    def actor_enters(self, actor, door_id=None):
        self.actors[actor.actor_id] = actor
        actor.room = self
        if door_id:
            actor.set_position(self.actors[door_id].position())
        else:
            entry_x = self.position[0] + self.width / 2
            entry_y = self.position[1] + self.height / 2
            actor.set_position((entry_x, entry_y))

    def actor_exits(self, actor):
        self.actors.pop(actor.actor_id)
        actor.room = None

    def exit_through_door(self, actor, door_id):
        door = self.actors[door_id]
        self.actor_exits(actor)
        door.exit_room.actor_enters(actor, door.exit_door_id)

    def all_doors(self):
        return filter(lambda r: type(r) is Door, self.actors.values())

    def left(self):
        return self.position[0]

    def top(self):
        return self.position[1]

    def right(self):
        return self.position[0] + self.width

    def bottom(self):
        return self.position[1] + self.height

    def wall_positions(self):
        return (self.left(), self.top(), self.right(), self.bottom())
