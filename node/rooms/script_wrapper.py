
import logging
log = logging.getLogger("rooms.node")


_scripts = dict()
_actor_info = dict()


class Script(object):
    def __init__(self, script_name):
        self.script_name = script_name
        try:
            _scripts[script_name] = __import__(script_name,
                fromlist=[script_name.rsplit(".", 1)])
        except:
            log.exception("Script %s is corrupt - cannot load", script_name)

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

    def is_request(self, method):
        return getattr(getattr(self.script_module, method), "is_request", False)

    def call_event_method(self, event_id, actor, *args, **kwargs):
        try:
            if event_id in self.events:
                getattr(self.script_module, event_id)(actor, *args, **kwargs)
        except:
            log.exception("Exception calling event %s in script %s", event_id,
                self.script_name)
            raise

    def call_method(self, method, actor, *args, **kwargs):
        try:
            log.debug("Calling method %s(%s, %s) in script %s", method, args,
                kwargs, self.script_name)
            return getattr(self.script_module, method)(actor, *args, **kwargs)
        except:
            log.exception("Exception calling method %s in script %s", method,
                self.script_name)
            raise

    def can_call(self, actor, command):
        filters = getattr(self.script_module, command).filters or dict()
        for key, value in filters.items():
            if actor.state.get(key, None) != value:
                return False
        return True
