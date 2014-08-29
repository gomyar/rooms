
from rooms.position import Position
import import_library


def move_to(actor, x, y):
    actor.move_to(Position(x, y))

def ping(actor):
    print "PING"
    for i in range(10):
        actor._send_update({"count": i})
        actor.sleep(1)

def test(actor):
    import_library.do_something(actor)
    return "loaded"
