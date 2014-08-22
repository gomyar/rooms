
import unittest

from rooms.state import SyncDict
from rooms.state import SyncList


class MockActor(object):
    def __init__(self):
        self.updates = 0

    def _send_update(self):
        self.updates += 1


class StateTest(unittest.TestCase):
    def setUp(self):
        self.actor = MockActor()
        self.state = SyncDict()
        self.state._set_actor(self.actor)

    def testSetValue(self):
        self.state['name1'] = "value1"
        self.assertEquals(1, self.actor.updates)

        self.state.name2 = "value2"
        self.assertEquals(2, self.actor.updates)

    def testSetChildValue(self):
        self.state['inner'] = SyncDict()

        self.assertEquals(1, self.actor.updates)

        self.state['inner']['field1'] = "value1"

        self.assertEquals(2, self.actor.updates)

    def testWrapBasicTypes(self):
        self.state['list_field'] = SyncList([1, 2, 3])

        self.assertEquals(1, self.actor.updates)

        self.state.list_field[1] = 15

        self.assertEquals(2, self.actor.updates)

        self.assertEquals(1, self.state.list_field[0])
        self.assertEquals(15, self.state.list_field[1])
        self.assertEquals(3, self.state.list_field[2])

        self.state.list_field.append(11)

        self.assertEquals(11, self.state.list_field[3])
        self.assertEquals(3, self.actor.updates)

    def testWrapDict(self):
        self.state['dict_field'] = SyncDict({'a': 1, 'b': 2, 'c': 3})

        self.assertEquals(1, self.actor.updates)

        self.state.dict_field['b'] = 15

        self.assertEquals(2, self.actor.updates)

        self.assertEquals(1, self.state.dict_field['a'])
        self.assertEquals(15, self.state.dict_field['b'])
        self.assertEquals(3, self.state.dict_field['c'])

    def testSetActor(self):
        self.actor2 = MockActor()

        self.state.inner = SyncDict({})

        self.assertEquals(1, self.actor.updates)

        self.state._set_actor(self.actor2)

        self.state.inner.child = "value"

        self.assertEquals(1, self.actor2.updates)

    def testEq(self):
        self.state.inner = SyncDict({})
        self.state.inner.child = "value"

        self.assertEquals({"inner": {"child": "value"}}, self.state)
