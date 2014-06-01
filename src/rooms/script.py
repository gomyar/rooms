
import os


class Script(object):
    def __init__(self, script_module):
        self.script_name = script_module
        self._import_script_module(script_module)

    def _import_script_module(self, script_module):
        self._script_module = __import__(script_module,
            fromlist=[script_module.rsplit(".", 1)])

    def call(self, method, *args, **kwargs):
        if self.has_method(method):
            return getattr(self._script_module, method)(*args, **kwargs)
        else:
            return None

    def has_method(self, method):
        return self._script_module and hasattr(self._script_module, method)


class NullScript(Script):
    def __init__(self):
        self.script_name = ""

    def call(self, method, *args, **kwargs):
        pass

    def has_method(self, method):
        return False
