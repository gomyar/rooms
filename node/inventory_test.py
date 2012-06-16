
import unittest

from inventory import Inventory
from inventory import Item


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory()

    def testAddItem(self):
        item = Item()
        item.variable = "value"
        self.inventory.add_item(item)

        self.assertEquals([item], self.inventory.all_items())
