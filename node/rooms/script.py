
class Script(object):
    def __init__(self, script_name):
        self.script_name = script_name
        self.script_module = __import__(script_name,
            fromlist=[script_name.rsplit(".", 1)])

    def __getattr__(self, name):
        return getattr(self.script_module, name, None)

    def all_methods(self):
        return []

    def has_method(self, method):
        return hasattr(self.script_module, method)

    def call_event_method(self, method, *args, **kwargs):
        if self.has_method(method):
            getattr(self.script_module, method)(*args, **kwargs)
