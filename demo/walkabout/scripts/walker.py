
from rooms.position import Position


def created(actor):
    actor.actor_type = "player"
    actor.model_type = "player"


def move_to(actor, x, y):
    actor.move_to(Position(x, y))
