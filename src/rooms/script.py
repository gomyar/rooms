
import os
import inspect
from functools import wraps


def command(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_command = True
    wrapped.args = inspect.getargspec(func).args
    return wrapped


def request(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_request = True
    wrapped.args = inspect.getargspec(func).args
    return wrapped


def action(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_request = True
    wrapped.args = inspect.getargspec(func).args
    return wrapped




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

    def inspect(self):
        methods = {}
        for field, func in inspect.getmembers(self.script_module, \
                predicate=inspect.isfunction):
            argspec = inspect.getargspec(func)
            methods[field] = {'args': argspec.args,
                'doc': func.__doc__ or "",
                'type': 'request'}
        return methods




class NullScript(Script):
    def __init__(self):
        self.script_name = ""
        self.script_module = None

    def call(self, method, *args, **kwargs):
        pass

    def has_method(self, method):
        return False

    def inspect(self):
        return {}
