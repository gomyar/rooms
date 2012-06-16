
import unittest

from inventory import Inventory
from inventory import Item
from inventory import create_item


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory()

    def testAddItem(self):
        item = Item()
        item.variable = "value"
        self.inventory.add_item(item)

        self.assertEquals([item], self.inventory.all_items())

    def testFindByProperties(self):
        item1 = create_item(name="bob", desc="this")
        item2 = create_item(name="fred", desc="this")
        item3 = create_item(name="bob", desc="that")
        self.inventory.add_item(item1)
        self.inventory.add_item(item2)
        self.inventory.add_item(item3)

        self.assertEquals([item1, item2],
            self.inventory.find_items(desc="this"))
        self.assertEquals([item1, item3],
            self.inventory.find_items(name="bob"))
        self.assertEquals([],
            self.inventory.find_items(name="fred", desc="that"))