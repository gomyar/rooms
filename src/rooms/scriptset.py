
import os
import sys
import imp

from rooms.script import Script
from rooms.script import NullScript


class ScriptSet(object):
    def __init__(self):
        self.scripts = dict()

    def load_scripts(self, script_path):
        sys.path.append(script_path)
        for py_file in self._list_scripts(script_path):
            script_name = os.path.splitext(py_file)[0]
            self.scripts[script_name] = Script(script_name,
                imp.load_source("rooms.scripts" + script_name,
                os.path.join(script_path, py_file)))

    def inspect_script(self, script_name):
        return self[script_name].inspect()

    def _list_scripts(self, script_path):
        return [path for path in os.listdir(script_path) if \
            path.endswith(".py") and path!= "__init__.py"]

    def __getitem__(self, name):
        return self.scripts.get(name, NullScript())

    def __setitem__(self, name, value):
        self.scripts[name] = value
