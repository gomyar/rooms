import math
import time
import inspect


def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def get_now():
    return time.time()


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


class Actor(object):
    def __init__(self, actor_id, x = 0, y = 0):
        self.actor_id = actor_id
        self.path = []
        self.set_position(x, y)
        self.speed = 200.0
        self.room = None
        self.instance = None
        self.state = "idle"
        self.log = []

    def __eq__(self, rhs):
        return rhs and type(rhs) == type(self) and rhs.actor_id == self.actor_id

    def __repr__(self):
        return "<Actor %s>" % (self.actor_id,)

    def interface_call(self, func_name, player, *args, **kwargs):
        func = getattr(self, func_name)
        if not self._can_call_method(player, func_name):
            raise Exception("Illegal call to %s in %s" % (func_name, self))
        return func(player, *args, **kwargs)

    def command_call(self, func_name, *args, **kwargs):
        func = getattr(self, func_name)
        if not self._can_call_command(func_name):
            raise Exception("Illegal call to %s in %s" % (func_name, self))
        return func(*args, **kwargs)

    def external(self):
        return dict(actor_id=self.actor_id, path=self.path, speed=self.speed)

    def x(self):
        now = get_now()
        if now > self.path[-1][2]:
            return self.path[-1][0]
        index = 0
        while index < len(self.path) -2 and self.path[index][2] < now:
            index += 1

        start_x, start_y, start_time = self.path[index]
        end_x, end_y, end_time = self.path[index + 1]

        if now > end_time:
            return end_x
        diff_x = end_x - start_x
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_x
        inc = (now - start_time) / diff_t
        return start_x + diff_x * inc

    def y(self):
        now = get_now()
        if now > self.path[-1][2]:
            return self.path[-1][1]
        index = 0
        while index < len(self.path) -2 and self.path[index][2] < now:
            index += 1

        start_x, start_y, start_time = self.path[index]
        end_x, end_y, end_time = self.path[index + 1]

        if now > end_time:
            return end_y
        diff_y = end_y - start_y
        diff_t = end_time - start_time
        if diff_t <= 0:
            return end_y
        inc = (now - start_time) / diff_t
        return start_y + diff_y * inc

    def set_position(self, x, y):
        self.path = [ (x, y, get_now() ), (x, y, get_now() ) ]

    def set_path(self, path):
        self.path = []
        last_x, last_y = path.pop(0)
        current_time = get_now()
        self.path.append( (last_x, last_y, current_time ) )
        while path:
            x, y = path.pop(0)
            current_time += self.time_to_move(last_x, last_y, x, y)
            self.path.append( (x, y, current_time ) )
            last_x, last_y = x, y

    def time_to_move(self, x1, y1, x2, y2):
        return distance(x1, y1, x2, y2) / self.speed

    def _filters_equal(self, actor, filters):
        for key, val in filters.items():
            if getattr(actor, key) != val:
                return False
        return True

    def _can_call_method(self, actor, method_name):
        func = getattr(self, method_name)
        return hasattr(func, "is_exposed") and \
            self._filters_equal(self, func.filters)

    def _can_call_command(self, method_name):
        func = getattr(self, method_name)
        return hasattr(func, "is_command") and \
            self._filters_equal(self, func.filters)

    def _all_exposed_methods(self, actor):
        return [m for m in dir(self) if self._can_call_method(actor, m)]

    def _all_exposed_commands(self):
        return [m for m in dir(self) if self._can_call_command(m)]

    def exposed_methods(self, actor):
        return [dict(name=method) for method in \
            self._all_exposed_methods(actor)]

    def exposed_commands(self):
        return [dict(name=command) for command in self._all_exposed_commands()]

    def add_log(self, msg, *args):
        log_entry = { 'msg': msg % args, 'time': time.time() }
        self.log.append(log_entry)
        self.instance.send_event(self.actor_id, "log", log_entry)

    def add_chat_message(self, msg, *args):
        self.add_log(msg, *args)
