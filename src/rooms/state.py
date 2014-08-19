
class State(dict):
    def __init__(self):
        super(State, self).__init__()

    def _set_actor(self, actor):
        self.__dict__['actor'] = actor

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value

    def __getitem__(self, name):
        return self.get(name, None)

    def __setitem__(self, name, value):
        super(State, self).__setitem__(name, value)
        if isinstance(value, State):
            value._set_actor(self.__dict__['actor'])
        self.actor._send_update()
