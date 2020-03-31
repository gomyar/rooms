from functools import wraps


def request(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_request = True
    wrapped.args = inspect.getargspec(func).args
    return wrapped


def websocket(func):
    @wraps(func)
    def wrapped(ws, *args, **kwargs):
        return func(ws, *args, **kwargs)
    wrapped.is_websocket = True
    wrapped.args = inspect.getargspec(func).args[1:]
    return wrapped
