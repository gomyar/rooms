
import random
import math

from rooms.script import *
from rooms.position import Position

import logging
log = logging.getLogger("rooms.player")


def player_joins(player, start_state):
    log.info("Created %s", player)
    player.speed = 10
    player.state.start_state = start_state


@command
def move_to(player, x, y):
    log.info("Moving to %s, %s", x, y)
    player.move_to(Position(int(x), int(y)))


@command
def set_position(player, x, y):
    player.position = Position(int(x), int(y))


@command
def add_item_to_inventory(player, item_type):
    player.inventory.add_item(item_type)
    player.lookup_items(category="commodity")
    player.state.added = True
