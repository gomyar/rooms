
from rooms.script import *

@expose
def pick_up(item, player):
    player.inventory.add_item(item.item_type)
    item.remove()
