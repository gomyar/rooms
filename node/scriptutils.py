
import sys

GAME_ROOT = "/home/ray/projects/rooms/games/demo1/"
if GAME_ROOT not in sys.path:
    sys.path.append(GAME_ROOT + "scripts")

def load_script(script_class):
    return __import__(script_class)
