
from rooms.position import Position


def player_joins(player, room):
    room.create_actor("rooms.test_scripts.basic_actor")


def move_to(actor, x, y):
    actor.move_to(Position(x, y))
