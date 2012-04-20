import math
import time
import inspect


def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def get_now():
    return time.time()


def expose(func):
    func.is_exposed = True
    def call(*args, **kwargs):
        return func(*args, **kwargs)
    call.is_exposed = True
    return call

def command(func):
    func.is_command = True
    def call(*args, **kwargs):
        return func(*args, **kwargs)
    call.is_command = True
    return call

class Actor(object):
    def __init__(self, player_id, x = 0, y = 0):
        self.player_id = player_id
        self.set_position(x, y)
        self.speed = 200.0
        self.room = None
        self.instance = None
        self.state = "idle"

    def interface_call(self, func_name, player, *args, **kwargs):
        func = getattr(self, func_name)
        if not hasattr(func, "is_exposed"):
            raise Exception("Illegal call to %s in %s", func_name, self)
        return func(player, *args, **kwargs)

    def command_call(self, func_name, *args, **kwargs):
        func = getattr(self, func_name)
        if not hasattr(func, "is_command"):
            raise Exception("Illegal call to %s in %s", func_name, self)
        return func(*args, **kwargs)

    def external(self):
        return dict(player_id=self.player_id, path=self.path, speed=self.speed)

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

    def _all_exposed_methods(self):
        all_members = dir(self)
        members = []
        for m in all_members:
            if hasattr(getattr(self, m), "is_exposed"):
                members.append(m)
        return members

    def _all_exposed_commands(self):
        all_members = dir(self)
        members = []
        for m in all_members:
            if hasattr(getattr(self, m), "is_command"):
                members.append(m)
        return members

    def exposed_methods(self, actor):
        return [dict(name=method) for method in self._all_exposed_methods()]

    def exposed_commands(self):
        return [dict(name=command) for command in self._all_exposed_commands()]

    def add_chat_message(self, msg, *args):
        self.instance.send_message(self.player_id, msg % args)
