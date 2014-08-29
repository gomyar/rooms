
import unittest
import os

from rooms.scriptset import ScriptSet
from rooms.script import NullScript
from rooms.testutils import MockActor


class ScriptSetTest(unittest.TestCase):
    def setUp(self):
        self.scriptset = ScriptSet()
        self.actor = MockActor()

    def testLoadScriptsFromPath(self):
        script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
            "test_scripts")
        self.scriptset.load_scripts(script_path)

        self.assertEquals("loaded", self.scriptset.scripts['basic_actor'].call("test", self.actor))
        self.assertEquals({
            'move_to':
                {'args': ['actor', 'x', 'y'], 'doc': '', 'type': 'request'},
            'ping': {'args': ['actor'], 'doc': '', 'type': 'request'},
            'test': {'args': ['actor'], 'doc': '', 'type': 'request'}},
            self.scriptset.inspect_script("basic_actor"))

    def testNullScript(self):
        self.assertEquals(NullScript, type(self.scriptset['nonexist']))

    def testImportLibrariesFromScripts(self):
        script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
            "test_scripts")
        self.scriptset.load_scripts(script_path)

        self.scriptset.scripts['basic_actor'].call("test", self.actor)

        self.assertEquals("set", self.actor.state.something)
