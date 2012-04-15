import math
import time

def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def get_now():
    return time.time()

def expose(func):
    Actor.exposed_methods.add(func.__name__)
    def call(*args, **kwargs):
        return func(*args, **kwargs)
    return call

class Actor(object):
    exposed_methods = set()

    def __init__(self, player_id, x = 0, y = 0):
        self.player_id = player_id
        self.path = [ (x, y, get_now() ), (x, y, get_now() ) ]
        self.speed = 200.0
        self.room = None

    def interface_call(self, func_name, *args, **kwargs):
        if func_name not in Actor.exposed_methods:
            raise Exception("Illegal call to %s in %s", func_name, self)
        return getattr(self, func_name)(*args, **kwargs)

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

class PlayerActor(Actor):
    def __init__(self, player_id, x = 0, y = 0):
        super(PlayerActor, self).__init__(player_id, x, y)

    @expose
    def walk_to(self, x, y):
        x, y = float(x), float(y)
        self.set_path([ (self.x(), self.y()), (x, y) ])

    @expose
    def boo(self):
        return "Boo"

    def moo(self):
        return "Moo"
