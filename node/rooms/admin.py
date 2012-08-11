
import os


class Admin(object):
    def __init__(self, game_root):
        self.game_root = game_root

    def list_scripts(self):
        dirlist = os.listdir(os.path.join(self.game_root, "scripts"))
        return [f for f in dirlist if f.endswith(".py")]

    def load_script(self, script_file):
        return open(os.path.join(self.game_root, "scripts", script_file)).read()

    def save_script(self, script_file, script_contents):
        try:
            script = open(os.path.join(self.game_root, "scripts", script_file), "w")
            script.write(script_contents)
        finally:
            script.close()
