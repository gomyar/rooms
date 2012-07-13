
import eventlet


class expose:
    def __init__(self, **filters):
        self.filters = filters

    def __call__(self, func):
        func.is_exposed = True
        func.filters = self.filters
        return func


class command:
    def __init__(self, **filters):
        self.filters = filters

    def __call__(self, func):
        func.is_command = True
        func.filters = self.filters
        return func


def sleep(seconds):
    eventlet.sleep(seconds)
