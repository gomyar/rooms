
from functools import wraps


_scripts = dict()

def expose(func=None, **filters):
    if func==None:
        def inner(func):
            return expose(func, **filters)
        return inner
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_exposed = True
    wrapped.filters = filters
    return wrapped


def command(func=None, **filters):
    if func==None:
        def inner(func):
            return command(func, **filters)
        return inner
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_command = True
    wrapped.filters = filters
    return wrapped


def event(func=None):
    if func==None:
        def inner(func):
            return event(func)
        return inner
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_event = True
    return wrapped


class Script(object):
    def __init__(self, script_name):
        self.script_name = script_name
        _scripts[script_name] = __import__(script_name,
            fromlist=[script_name.rsplit(".", 1)])

    def __getattr__(self, name):
        return getattr(self.script_module, name, None)

    @property
    def methods(self):
        return [m for m in dir(self.script_module) if \
            getattr(getattr(self.script_module, m), "is_exposed", None)]

    @property
    def events(self):
        return [m for m in dir(self.script_module) if \
            getattr(getattr(self.script_module, m), "is_event", None)]

    @property
    def script_module(self):
        return _scripts[self.script_name]

    @property
    def commands(self):
        return [m for m in dir(self.script_module) if \
            getattr(getattr(self.script_module, m), "is_command", None)]

    def has_method(self, method):
        return hasattr(self.script_module, method)

    def call_event_method(self, event_id, actor, *args, **kwargs):
        if event_id in self.events:
            getattr(self.script_module, event_id)(actor, *args, **kwargs)

    def can_call(self, actor, command):
        filters = getattr(self.script_module, command).filters or dict()
        for key, value in filters.items():
            if actor.state.get(key, None) != value:
                return False
        return True