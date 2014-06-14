
from rooms.position import Position


def created(actor):
    actor.state['created'] = True

def player_joins(player_actor, room):
    player_actor.state.initialized = True

def move_to(actor, x, y):
    actor.move_to(Position(x, y))

def ping(actor):
    print "PING"
    for i in range(10):
        actor._send_update({"count": i})
        actor.sleep(1)
