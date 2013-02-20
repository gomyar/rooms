
import unittest

from rooms.script_wrapper import Script
from script import command

from rooms.actor import Actor


@command
def first_command(actor, param1):
    actor.state.param1 = param1

@command
def second_command(actor, param1):
    actor.state.param1 = param1


class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.script = Script("rooms.script_wrapper_test")
        self.actor = Actor("actor1")
        self.actor.script = self.script
        self.actor2 = Actor("actor2")

    def testFirstCommand(self):
        self.assertEquals([{
            'args': ['actor', 'param1'],
            'name': 'first_command'
        },
        {
            'args': ['actor', 'param1'],
            'name': 'second_command'
        }],
            self.script.commands())

        self.actor.call_command('first_command', "value1")

        self.assertEquals(("first_command", [self.actor, "value1"], {}),
            self.actor.method_call)

        self.actor._process_queue_item()

        self.assertEquals("value1", self.actor.state.param1)
