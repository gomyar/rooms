
import unittest

from rooms.script import Script


def script_call(field):
    return "test %s" % field


class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.script = Script()
        self.script.load_script("rooms.script_test")

    def testLoad(self):
        self.assertEquals("test val", self.script.call("script_call", "val"))
