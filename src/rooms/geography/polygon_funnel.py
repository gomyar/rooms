

from .basic_geography import BasicGeography


class Vertex(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.previous = None
        self.next = None


class PolygonFunnel(BasicGeography):
    def get_vertices(self, room):
        return 
