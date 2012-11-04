
import random

def roll(actor, stats, target):
    result = random.randint(1, 20)
    for stat in stats:
        result += actor.state[stat]
    return result >= target
