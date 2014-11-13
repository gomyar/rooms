
from rooms.position import Position
import random

import logging
log = logging.getLogger("npc")


def created(actor):
    actor.speed = 50


def kickoff(actor):
    print "Running kickoff for %s" % (actor,)
    while True:
        log.debug("kickoff for actor %s in room %s", actor, actor.room)
        for x, y in [(-10, -10), (10, -10), (10, 10), (-10, 10)]:
            actor.move_wait(actor.room.center.add_coords(x, y))
        door = random.choice(actor.room.doors)
        actor.move_wait(door.enter_position)
        actor.enter(door)