
import unittest

from rooms.state import State


class MockActor(object):
    def __init__(self):
        self.updates = 0

    def _send_update(self):
        self.updates += 1


class StateTest(unittest.TestCase):
    def setUp(self):
        self.actor = MockActor()
        self.state = State()
        self.state._set_actor(self.actor)

    def testSetValue(self):
        self.state['name1'] = "value1"
        self.assertEquals(1, self.actor.updates)

        self.state.name2 = "value2"
        self.assertEquals(2, self.actor.updates)

    def testSetChildValue(self):
        self.state['inner'] = State()

        self.assertEquals(1, self.actor.updates)

        self.state['inner']['field1'] = "value1"

        self.assertEquals(2, self.actor.updates)
