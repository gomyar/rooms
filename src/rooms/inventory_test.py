
import unittest

from inventory import Inventory
from inventory import Item
from inventory import create_item
from inventory import register_item


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory()

    def testAddItem(self):
        item = Item("item1")
        item.variable = "value"
        register_item(item)
        self.inventory.add_item("item1")

        self.assertEquals(dict(item1=1), self.inventory.all_items())

    def testFindByProperties(self):
        item1 = create_item("item1", name="bob", desc="this")
        item2 = create_item("item2", name="fred", desc="this")
        item3 = create_item("item3", name="bob", desc="that")
        register_item(item1)
        register_item(item2)
        register_item(item3)
        self.inventory.add_item("item1")
        self.inventory.add_item("item2")
        self.inventory.add_item("item3")

        found = self.inventory.find_items(desc="this")
        self.assertTrue(item1 in found)
        self.assertTrue(item2 in found)

        found = self.inventory.find_items(name="bob")
        self.assertTrue(item1 in found)
        self.assertTrue(item3 in found)

        self.assertEquals([],
            self.inventory.find_items(name="fred", desc="that"))

    def testSomething(self):
        register_item(Item("jade_monkey"))
        self.inventory.add_item("jade_monkey")

        self.assertEquals({'jade_monkey': 1}, self.inventory.all_items())

    def testCollection(self):
        self.inventory.add_item("jade_monkey")

        self.assertTrue("jade_monkey" in self.inventory)
        self.assertFalse("nothing" in self.inventory)
