
import unittest
import os

from rooms.scriptset import ScriptSet
from rooms.script import NullScript


class ScriptSetTest(unittest.TestCase):
    def setUp(self):
        self.scriptset = ScriptSet()

    def testLoadScriptsFromPath(self):
        script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
            "test_scripts")
        self.scriptset.load_scripts(script_path)

        self.assertEquals("loaded", self.scriptset.scripts['basic_actor'].call("test"))
        self.assertEquals({
            'move_to':
                {'args': ['actor', 'x', 'y'], 'doc': '', 'type': 'request'},
            'ping': {'args': ['actor'], 'doc': '', 'type': 'request'},
            'test': {'args': [], 'doc': '', 'type': 'request'}},
            self.scriptset.inspect_script("basic_actor"))

    def testNullScript(self):
        self.assertEquals(NullScript, type(self.scriptset['nonexist']))
