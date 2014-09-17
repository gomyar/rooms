
import unittest

from rooms.visibility_filter import VisibilityFilter
from rooms.testutils import MockActor


class MockListener(object):
    def __init__(self):
        self.update_log = []

    def actor_update(self, actor):
        self.update_log.append(('update', actor))

    def remove_actor(self, actor):
        self.update_log.append(('remove', actor))


class VisibilityFilterTest(unittest.TestCase):
    def setUp(self):
        self.visibility_filter = VisibilityFilter()
        self.listener = MockListener()
        self.visibility_filter.add_listener(self.listener)

        self.actor1 = MockActor("actor1")
        self.actor2 = MockActor("actor2")

    def testBasicUpdate(self):
        self.visibility_filter.actor_state_changed(self.actor1)
        self.assertEquals([('update', self.actor1)], self.listener.update_log)

        self.visibility_filter.actor_state_changed(self.actor2)
        self.assertEquals([('update', self.actor1), ('update', self.actor2)],
            self.listener.update_log)

        self.visibility_filter.actor_state_changed(self.actor2)
        self.assertEquals([('update', self.actor1), ('update', self.actor2),
            ('update', self.actor2)],
            self.listener.update_log)

        self.visibility_filter.actor_removed(self.actor1)
        self.assertEquals([('update', self.actor1), ('update', self.actor2),
            ('update', self.actor2), ('remove', self.actor1)],
            self.listener.update_log)

        self.visibility_filter.actor_becomes_invisible(self.actor1)
        self.assertEquals([('update', self.actor1), ('update', self.actor2),
            ('update', self.actor2), ('remove', self.actor1),
            ('remove', self.actor1)],
            self.listener.update_log)

        self.visibility_filter.actor_becomes_visible(self.actor1)
        self.assertEquals([('update', self.actor1), ('update', self.actor2),
            ('update', self.actor2), ('remove', self.actor1),
            ('remove', self.actor1), ('update', self.actor1)],
            self.listener.update_log)

        self.visibility_filter.actor_added(self.actor1)
        self.assertEquals([('update', self.actor1), ('update', self.actor2),
            ('update', self.actor2), ('remove', self.actor1),
            ('remove', self.actor1), ('update', self.actor1),
            ('update', self.actor1)],
            self.listener.update_log)

