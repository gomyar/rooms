
import random

def roll(actor, stats, target):
    result = random.randint(1, 20)
    for stat in stats:
        result += actor.get_stat(stat)
    return result >= target
