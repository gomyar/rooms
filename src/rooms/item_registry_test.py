
import unittest
import os

from rooms.item_registry import ItemRegistry
from rooms.item_registry import Item


class ItemRegistryTest(unittest.TestCase):
    def setUp(self):
        self.registry = ItemRegistry()

    def test_load(self):
        self.registry.load_from_json(open(os.path.join(
            os.path.dirname(__file__), "test_items", "cutlery_items.json")
            ).read())

        self.assertEquals(["cutlery"], self.registry.get_categories())
        self.assertEquals(3, len(self.registry.items_by_category("cutlery")))

    def testAllItems(self):
        self.registry.load_from_json(open(os.path.join(
            os.path.dirname(__file__), "test_items",
            "cutlery_categories.json")).read())

        cup = Item("general", "cup", dict(size="medium"))
        saucer = Item("general", "saucer", dict(size="small"))
        spoon = Item("specific", "spoon", dict(size="medium"))

        self.assertTrue(cup in self.registry.items_by_category("general"))
        self.assertTrue(saucer in self.registry.items_by_category("general"))
        self.assertEquals([spoon], self.registry.items_by_category("specific"))

        self.assertEquals([cup], self.registry.items_by_category("general",
            size="medium"))
