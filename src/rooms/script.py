
import os


class Script(object):
    def __init__(self, script_name, script_module):
        self.script_name = script_name
        self.script_module = script_module

    def __repr__(self):
        return "<Script %s - %s>" % (self.script_name, self.script_module)

    def call(self, method, *args, **kwargs):
        if self.has_method(method):
            return getattr(self.script_module, method)(*args, **kwargs)
        else:
            return None

    def has_method(self, method):
        return self.script_module and hasattr(self.script_module, method)


class NullScript(Script):
    def __init__(self):
        pass

    def call(self, method, *args, **kwargs):
        pass

    def has_method(self, method):
        return False
