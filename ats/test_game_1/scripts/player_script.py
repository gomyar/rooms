
import random
import math

from rooms.script import *

def created(player_actor):
    log.info("Created %s", player_actor)
    player_actor.speed = 100

@command
def move_to(player, x, y):
    log.info("Moving to %s, %s", x, y)
    player.move_to(int(x), int(y))

@command
def set_position(player, x, y):
    player.set_position((int(x), int(y)))