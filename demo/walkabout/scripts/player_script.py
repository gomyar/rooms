
from rooms.position import Position


def created(player_actor):
    print ("Creating walker")
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
    player_actor.state.log = []
    spawn_locations = player_actor.room.find_tags("player.spawn")
    if spawn_locations:
        player_actor.position = spawn_locations[0].position


def move_to(actor, x, y):
#    actor.state.log.append("Moving to %s, %s" % (x, y))
    actor.state.speed = 10
    print ("Moving from %s to %s, %s" % (actor.position, x, y))
    actor.move_to(Position(x, y))


def exit_through_door(actor, exit_room_id):
#    actor.state.log.append("Moving to door %s" % (exit_room_id,))
    door = actor.room.get_door(exit_room_id=exit_room_id)
    actor.move_wait(door.position)
#    actor.state.log.append("Entering door %s" % (exit_room_id,))
    actor.enter(door)
