
from rooms.position import Position


def created(actor):
    actor.speed = 50


def kickoff(actor):
    print "Running kickoff for %s" % (actor,)
    while True:
        actor.move_wait(Position(actor.room.topleft.x + 10, 10))
        actor.move_wait(Position(actor.room.topleft.x + 450, 450))
