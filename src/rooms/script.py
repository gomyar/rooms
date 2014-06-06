
import os


class Script(object):
    def __init__(self, script_name):
        self.script_name = script_name
        self._script_module = None

    def _lazy_import_script(self):
        if not self._script_module:
            self._script_module= __import__(self.script_name,
                fromlist=[self.script_name.rsplit(".", 1)])

    def call(self, method, *args, **kwargs):
        self._lazy_import_script()
        if self.has_method(method):
            return getattr(self._script_module, method)(*args, **kwargs)
        else:
            return None

    def has_method(self, method):
        self._lazy_import_script()
        return self._script_module and hasattr(self._script_module, method)


class NullScript(Script):
    def __init__(self):
        self.script_name = ""

    def call(self, method, *args, **kwargs):
        pass

    def has_method(self, method):
        return False
