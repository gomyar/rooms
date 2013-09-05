
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


