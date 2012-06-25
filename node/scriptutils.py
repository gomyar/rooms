
import sys

GAME_ROOT = "/home/ray/projects/rooms/games/dungeon/"
if GAME_ROOT not in sys.path:
    sys.path.append(GAME_ROOT)

def load_script(script_class):
    module = __import__("scripts.%s" % (script_class,),
        fromlist=['scripts'])
    return getattr(module, script_class)()
