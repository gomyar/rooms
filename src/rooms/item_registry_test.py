
import unittest

from item_registry import ItemRegistry
from item_registry import Item


class ItemRegistryTest(unittest.TestCase):
    def setUp(self):
        self.item_registry = ItemRegistry()

    def testFindByProperties(self):
        item1 = Item("item1", name="bob", desc="this")
        item2 = Item("item2", name="fred", desc="this")
        item3 = Item("item3", name="bob", desc="that")
        self.item_registry.add_item(item1)
        self.item_registry.add_item(item2)
        self.item_registry.add_item(item3)

        found = self.inventory.find_items(desc="this")
        self.assertTrue((item1, 1) in found)
        self.assertTrue((item2, 1) in found)

        found = self.inventory.find_items(name="bob")
        self.assertTrue((item1, 1) in found)
        self.assertTrue((item3, 1) in found)

        self.assertEquals([],
            self.inventory.find_items(name="fred", desc="that"))

