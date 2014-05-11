
import os


class Script(object):
    def __init__(self):
        self._script_module = None

    def load_script(self, script_module):
        self._script_module = __import__(script_module,
            fromlist=[script_module.rsplit(".", 1)])

    def call(self, method, *args, **kwargs):
        if self.has_method(method):
            return getattr(self._script_module, method)(*args, **kwargs)
        else:
            return None

    def has_method(self, method):
        return self._script_module and hasattr(self._script_module, method)
