

class Path(object):
    def __init__(self, waypoints=None):
        self.waypoints = waypoints or []

    def __repr__(self):
        return "<Path: %s>" % ([p for p in self.waypoints],)

    def __eq__(self, rhs):
        return rhs and type(rhs) == Path and self.waypoints == rhs.waypoints
