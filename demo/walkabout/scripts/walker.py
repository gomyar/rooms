
from rooms.position import Position


def created(actor):
    actor.speed = 100


def move_to(actor, x, y):
    actor.move_to(Position(x, y))


def exit_through_door(actor, exit_room_id):
    door = actor.room.get_door(exit_room_id=exit_room_id)
    actor.move_wait(door.position)
    actor.enter(door)
