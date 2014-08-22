
from rooms.position import Position


def player_joins(player_actor):
    print "Creating walker"
    player_actor.speed = 100
    player_actor.state.log = [
        "stuff",
        "n",
        "junk",
    ]
    player_actor.state.inventory = {
        "cakes": 10,
        "pancakes": 12,
        "syrup": 1,
        "salt": 15,
    }


def move_to(actor, x, y):
    actor.move_to(Position(x, y))


def exit_through_door(actor, exit_room_id):
    door = actor.room.get_door(exit_room_id=exit_room_id)
    actor.move_wait(door.enter_position)
    actor.enter(door)
