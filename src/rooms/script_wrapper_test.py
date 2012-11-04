
import unittest

from rooms.script_wrapper import Script
from script import command
from script import expose

from rooms.actor import Actor


@command
def first_command(actor, param1):
    actor.state.param1 = param1

@expose
def first_method(actor, player, param1):
    actor.state.param1 = param1

@command(call_second=True)
def second_command(actor, param1):
    actor.state.param1 = param1


class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.script = Script("rooms.script_wrapper_test")
        self.actor = Actor("actor1")
        self.actor.script = self.script
        self.actor2 = Actor("actor2")

    def testFirstCommand(self):
        self.assertEquals(['first_command', 'second_command'],
            self.script.commands)

        self.actor.command_call('first_command', "value1")

        self.assertEquals(("first_command", [self.actor, "value1"], {}),
            self.actor.call_queue.queue[0])

        self.actor._process_queue_item()

        self.assertEquals("value1", self.actor.state.param1)

    def testFirstMethod(self):
        self.assertEquals(['first_method'], self.script.methods)

        self.actor.interface_call('first_method', self.actor2, "value1")
        self.actor._process_queue_item()

        self.assertEquals("value1", self.actor.state.param1)

    def testCommandFilter(self):
        self.assertFalse(self.script.can_call(self.actor,
            "second_command"))

        self.actor.state.call_second = True

        self.assertTrue(self.script.can_call(self.actor,
            "second_command"))
