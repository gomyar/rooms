
import unittest

from inventory import Inventory


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory()

    def testSomething(self):
        self.inventory.add_item("jade_monkey")

        self.assertEquals({'jade_monkey': 1}, self.inventory.all_items())

    def testCollection(self):
        self.inventory.add_item("jade_monkey")

        self.assertTrue("jade_monkey" in self.inventory)
        self.assertFalse("nothing" in self.inventory)
