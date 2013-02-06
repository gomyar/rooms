
import inspect

import logging
log = logging.getLogger("rooms.node")


_scripts = dict()
_actor_scripts = dict()


def register_actor_script(script_name, actor):
    if script_name not in _actor_scripts:
        _actor_scripts[script_name] = []
    if actor is not _actor_scripts[script_name]:
        _actor_scripts[script_name].append(actor)

def deregister_actor_script(script_name, actor):
    if _actor_scripts and script_name in _actor_scripts:
        if actor in _actor_scripts[script_name]:
            _actor_scripts[script_name].remove(actor)
        if _actor_scripts[script_name] == []:
            _actor_scripts.pop(script_name)


class Script(object):
    def __init__(self, script_name):
        self.script_name = script_name
        try:
            _scripts[script_name] = __import__(script_name,
                fromlist=[script_name.rsplit(".", 1)])
        except:
            log.exception("Script %s is corrupt - cannot load", script_name)

    @property
    def script_module(self):
        return _scripts[self.script_name]

    def methods(self):
        return [self._describe(m) for m in dir(self.script_module) if \
            getattr(getattr(self.script_module, m), "is_exposed", None)]

    def commands(self):
        return [self._describe(m) for m in dir(self.script_module) if \
            getattr(self.get_method(m), "is_command", None)]

    def api(self):
        return dict(
            commands = [self._describe(m) for m in dir(self.script_module) if \
                getattr(self.get_method(m), "is_command", None)],
            requests = [self._describe(m) for m in dir(self.script_module) if \
                getattr(self.get_method(m), "is_request", None)],
        )

    def exposed_api(self):
        return dict(
            commands = [self._describe(m) for m in dir(self.script_module) if \
                getattr(self.get_method(m), "is_exposed_command", None)],
            requests = [self._describe(m) for m in dir(self.script_module) if \
                getattr(self.get_method(m), "is_exposed_request", None)],
        )

    def _describe(self, method_name):
        method = getattr(self.script_module, method_name)
        return {'name': method_name, 'args': method.args}

    def has_method(self, method):
        return hasattr(self.script_module, method)

    def is_request(self, method):
        return getattr(self.get_method(method), "is_request", False)

    def is_exposed_request(self, method):
        return getattr(self.get_method(method), "is_exposed_request", False)

    def call_method(self, method, actor, *args, **kwargs):
        return self.get_method(method)(actor, *args, **kwargs)

    def get_method(self, method):
        return getattr(self.script_module, method)

    def can_call(self, actor, command):
        filters = getattr(self.script_module, command).filters or dict()
        for key, value in filters.items():
            if actor.state.get(key, None) != value:
                return False
        return True
