
from pcscript import *


def kickoff(player):
    player.stats['hp'] = 10


@command()
def walk_to(player, x, y):
    player.move_to(x, y)


@expose()
def melee_attack(player, attacker):
    attacker.move_towards(player)

    attacker.perform_action("melee_attack", 1)
    if roll(attacker, ["str", "brawl"], 10):
        player.stats['hp'] -= 5
        player.perform_action("lost_hp", 0.2, hp=5)
