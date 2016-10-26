

class OnlineNode(object):
    def __init__(self, name, host):
        self.name = name
        self.host = host
        self.load = 0.0
        self.uptime = 0.0
