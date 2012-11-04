
import os
import sys
import traceback

from rooms.script_wrapper import _scripts
from rooms.script_wrapper import _actor_scripts


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

    def create_chat_script(self, script_file):
        if "/" in script_file:
            raise Exception("Slashes? we dont need no stinkin slashes")
        filepath = os.path.join(self.game_root, "scripts", script_file)
        if os.path.exists(filepath):
            raise Exception("File already exists")
        newfile = open("%s.json" % (filepath,), "w")
        newfile.write('{ "choices": []}')
        newfile.close()

    def save_script(self, script_file, script_contents):
        if "/" in script_file:
            raise Exception("Slashes? we dont need no stinkin slashes")
        try:
            script_path = os.path.join(self.game_root, "scripts", script_file)
            script = open(script_path, "w")
            script.write(script_contents)
            script.close()

            script_name = script_file.rstrip(".py")
            reload(_scripts[script_name])
            for actor in _actor_scripts[script_name]:
                actor.kick()
            return {'success': True}
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.format_exception(exc_type, exc_value,
                exc_traceback)
            stacktrace = [str(s) for s in stacktrace]
            stacktrace = "\n".join(stacktrace)
            return {'success': False, 'stacktrace':stacktrace}

    def save_chat_script(self, script_file, script_contents):
        if "/" in script_file:
            raise Exception("Slashes? we dont need no stinkin slashes")
        try:
            script_path = os.path.join(self.game_root, "scripts", script_file)
            script = open(script_path, "w")
            script.write(script_contents)
            script.close()

            return {'success': True}
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.format_exception(exc_type, exc_value,
                exc_traceback)
            stacktrace = [str(s) for s in stacktrace]
            stacktrace = "\n".join(stacktrace)
            return {'success': False, 'stacktrace':stacktrace}


    def add_choice(self, chat_script, request, response, function, *index):
        script = self.load_chat_script(chat_script)


    def delete_choice(self, chat_script, *index):
        pass

    def choice_move_up(self, chat_script, *index):
        pass

    def choice_move_down(self, chat_script, *index):
        pass

