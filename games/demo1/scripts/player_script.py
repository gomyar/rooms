
from script import *

@command
def list_inventory(player):
    return player.inventory.all_items()

def add_evidence(player, npc, category, description):
    evidence = create_item(npc_id=npc.actor_id, category=category,
        description=description)
    player.inventory.add_item(evidence)
    player.add_chat_message("You learned something about %s: %s" % (
        npc.actor_id, description))

def has_evidence(player, npc, category):
    return player.inventory.find_items(npc_id=npc.actor_id,
        category=category)

@command
def move_to(player, x, y):
    player.move_to(x, y)

@request
def leave_instance(player):
    player.leave_instance()

@command
def exit(player, door_id):
    player.exit(door_id)
