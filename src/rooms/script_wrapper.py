
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

    def __repr__(self):
        return "<Script %s>" % (self.script_name,)

    @property
    def script_module(self):
        return _scripts[self.script_name]

    def commands(self):
        return [self._describe(m) for m in dir(self.script_module) if \
            getattr(getattr(self, m), "is_command", None)]

    def api(self):
        return dict(
            commands = [self._describe(m) for m in dir(self.script_module) if \
                self.script.is_command(m)],
            requests = [self._describe(m) for m in dir(self.script_module) if \
                self.script.is_request(m)],
        )

    def _describe(self, method_name):
        method = getattr(self.script_module, method_name)
        return {'name': method_name, 'args': method.args}

    def is_request(self, method):
        return getattr(getattr(self, method), "is_request", False)

    def _call_function(self, function, *args, **kwargs):
        return getattr(self, function)(*args, **kwargs)

    def __getattr__(self, key):
        if key in self:
            return getattr(self.script_module, key)
        else:
            raise AttributeError("Function %s does not exist in script %s" % (
                key, self))

    def __contains__(self, key):
        return hasattr(self.script_module, key)
