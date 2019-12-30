
import unittest

from rooms.state import SyncState


class MockActor(object):
    def __init__(self):
        self.updates = []

    def _update_public_state(self, action, name, value):
        self.updates.append((action, name, value))


class StateTest(unittest.TestCase):
    def setUp(self):
        self.actor = MockActor()
        self.state = SyncState({}, self.actor._update_public_state)
        self.actor.state = self.state

    def testSetValue(self):
        self.state['name1'] = "value1"
        self.assertEquals([
            ('set', 'name1', 'value1'),
        ], self.actor.updates)

        self.state.name2 = "value2"

        self.assertEquals([
            ('set', 'name1', 'value1'),
            ('set', 'name2', 'value2'),
        ], self.actor.updates)

    def testSetChildValue(self):
        self.state['inner'] = {}

        self.assertEquals([
            ('set', 'inner', {}),
        ], self.actor.updates)

        self.state['inner']['field1'] = "value1"

        self.assertEquals([
            ('set', 'inner', {}),
            ('set', 'inner.field1', 'value1'),
        ], self.actor.updates)
        self.assertTrue('inner' in self.state)
        self.assertTrue('field1' in self.state['inner'])
        self.assertTrue('field1' in self.state.inner)

    def testWrapBasicTypes(self):
        self.state['list_field'] = [1, 2, 3]

        self.assertEquals([
            ("set", "list_field", [1, 2, 3]),
        ], self.actor.updates)

        self.state.list_field[1] = 15

        self.assertEquals([
            ("set", "list_field", [1, 2, 3]),
            ("set", "list_field.1", 15),
        ], self.actor.updates)

        self.assertEquals(1, self.state.list_field[0])
        self.assertEquals(15, self.state.list_field[1])
        self.assertEquals(3, self.state.list_field[2])

        self.state.list_field.append(11)

        self.assertEquals(11, self.state.list_field[3])

        self.assertEquals([
            ("set", "list_field", [1, 2, 3]),
            ("set", "list_field.1", 15),
            ("set", "list_field.3", 11),
        ], self.actor.updates)

    def testWrapDict(self):
        self.state['dict_field'] = {'a': 1, 'b': 2, 'c': 3, 'd': {'e': 5}}

        self.assertEquals([
            ('set', 'dict_field', {'a': 1, 'b': 2, 'c': 3, 'd': {'e': 5}}),
        ], self.actor.updates)

        self.state.dict_field['b'] = 15

        self.assertEquals([
            ('set', 'dict_field', {'a': 1, 'b': 2, 'c': 3, 'd': {'e': 5}}),
            ('set', 'dict_field.b', 15),
        ], self.actor.updates)

        self.state.dict_field['d']['e'] = 25

        self.assertEquals([
            ('set', 'dict_field', {'a': 1, 'b': 2, 'c': 3, 'd': {'e': 5}}),
            ('set', 'dict_field.b', 15),
            ('set', 'dict_field.d.e', 25),
        ], self.actor.updates)

        self.assertEquals(1, self.state.dict_field['a'])
        self.assertEquals(15, self.state.dict_field['b'])
        self.assertEquals(3, self.state.dict_field['c'])
        self.assertEquals(25, self.state.dict_field['d']['e'])

    def testPopDict(self):
        self.state['dict_field'] = {'a': 1, 'b': 2, 'c': 3}

        self.state.dict_field.pop('b')

        self.assertEquals([
            ('set', 'dict_field', {'a': 1, 'b': 2, 'c': 3}),
            ('pop', 'dict_field.b', None),
        ], self.actor.updates)

        self.assertEquals({'a': 1, 'c': 3}, self.state.dict_field)

    def testPopList(self):
        self.state['list_field'] = [1, 2, 3]

        self.state.list_field.pop(1)

        self.assertEquals([
            ('set', 'list_field', [1, 2, 3]),
            ('pop', 'list_field.1', None),
        ], self.actor.updates)

        self.assertEquals([1, 3], self.state.list_field)

    def testUnicodePoint(self):
        self.state['dict_field'] = {'a.b': 1}

        self.assertEquals([
            ('set', 'dict_field', {'a.b': 1})
        ], self.actor.updates)

    def testEq(self):
        self.state.inner = {}
        self.state.inner.child = "value"

        self.assertEquals({"inner": {"child": "value"}}, self.state)

    def testListSlices(self):
        self.state['list_field'] = [1, 2, 3]

        self.state['second_list'] = self.state.list_field[:2]

        self.assertEquals([
            ('set', 'list_field', [1, 2, 3]),
            ('set', 'second_list', [1, 2]),
        ], self.actor.updates)
        self.assertEquals(2, len(self.actor.state.second_list))
        self.assertEquals([1, 2], self.actor.state.second_list)

        self.actor.state.second_list.append(5)
        self.assertEquals([
            ('set', 'list_field', [1, 2, 3]),
            ('set', 'second_list', [1, 2]),
            ('set', 'second_list.2', 5),
        ], self.actor.updates)
        self.assertEquals(3, len(self.actor.state.second_list))
        self.assertEquals([1, 2, 5], self.actor.state.second_list)
