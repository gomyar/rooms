
import os
import inspect
from functools import wraps


def load_script(script_name):
    if not script_name:
        return NullScript()
    if '.' in script_name:
        modname = script_name[:script_name.rfind('.')]
    else:
        modname = script_name
    return Script(script_name, __import__(script_name, fromlist=[modname]))


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
            return self.get_method(method)(*args, **kwargs)
        else:
            return None

    def get_method(self, method):
        return getattr(self.script_module, method)

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

    def __getattr__(self, name):
        if self.has_method(name):
            return self.get_method(name)
        else:
            raise Exception("No such script function: %s" % (name,))


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
