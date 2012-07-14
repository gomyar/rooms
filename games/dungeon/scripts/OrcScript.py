
from pcscript import *


def kickoff(npc):
    npc.stats['hp'] = 10
    npc.set_state("hunting")

def state_hunting(npc):
    while True:
        walk_to_nearest_player(npc)
        sleep(3)

def walk_to_nearest_player(npc):
    player = npc.room.closest_player(npc.position())
    if player:
        npc.move_towards(player)
    else:
        sleep(5)

@expose()
def attack(npc, player):
    player.move_towards(npc)

    player.perform_action("melee_attack", 1)
    if player.roll(["str", "brawl"], 10):
        npc.stats['hp'] -= 5
        npc.perform_action("lost_hp", 0.2, hp=5)
        if npc.stats['hp'] <= 0:
            npc.remove()
