import unittest

from rooms.script import Script



class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.script = Script("script_test", ScriptTest)

    @staticmethod
    def script_call(field):
        return "test %s" % field

    def testLoad(self):
        self.assertEquals("test val", self.script.call("script_call", "val"))

    def testNoProblemIfNoScriptLoaded(self):
        self.assertEquals(None, self.script.call("nonexistant"))

    def testInspect(self):
        inspected = self.script.inspect()
        self.assertEquals(['field'], inspected['script_call']['args'])
        self.assertEquals('', inspected['script_call']['doc'])
        self.assertEquals('request', inspected['script_call']['type'])

    def testScriptFunctionAccess(self):
        self.assertEquals("test argle", self.script.script_call('argle'))
