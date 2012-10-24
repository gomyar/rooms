
from script import *

@expose
def pick_up(item, player):
    player.inventory.add_item(item)
