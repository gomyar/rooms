
import os
import sys
import traceback

from rooms.script import _scripts


class Admin(object):
    def __init__(self, game_root):
        self.game_root = game_root

    def list_scripts(self):
        dirlist = os.listdir(os.path.join(self.game_root, "scripts"))
        return dict(scripts=[f for f in dirlist if f.endswith(".py")],
            chat_scripts=[f for f in dirlist if f.endswith(".json")])

    def load_script(self, script_file):
        if "/" in script_file:
            raise Exception("Slashes? we dont need no stinkin slashes")
        return open(os.path.join(self.game_root, "scripts", script_file)).read()

    def load_chat_script(self, script_file):
        if "/" in script_file:
            raise Exception("Slashes? we dont need no stinkin slashes")
        return open(os.path.join(self.game_root, "scripts", script_file)).read()

    def save_script(self, script_file, script_contents):
        if "/" in script_file:
            raise Exception("Slashes? we dont need no stinkin slashes")
        try:
            script_path = os.path.join(self.game_root, "scripts", script_file)
            script = open(script_path, "w")
            script.write(script_contents)
            script.close()

            reload(_scripts[script_file.rstrip(".py")])
            return {'success': True}
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.format_exception(exc_type, exc_value,
                exc_traceback)
            stacktrace = [str(s) for s in stacktrace]
            stacktrace = "\n".join(stacktrace)
            return {'success': False, 'stacktrace':stacktrace}
