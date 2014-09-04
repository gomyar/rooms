
import unittest

from rooms.item_registry import ItemRegistry
from rooms.item_registry import Item
from rooms.game import Game
from testutils import MockContainer


class ItemRegistryTest(unittest.TestCase):
    def setUp(self):
        self.container = MockContainer()
        self.registry = ItemRegistry(self.container)

    def testRegistry(self):
        self.registry.add_item("general", "cup", dict(size="medium"))

        self.assertEquals({
            "__type__": "Item",
            "_id": "itemregistry_0",
            "category": "general", "item_type": "cup",
            "data": {"size": "medium"}},
            self.container.dbase.dbases['itemregistry']["itemregistry_0"])

        cup = Item("general", "cup", dict(size="medium"))
        self.assertEquals(cup, self.registry.get_item("general", "cup"))

        self.assertEquals([cup], self.registry.all_items("general"))

    def testAllItems(self):
        self.registry.add_item("general", "cup", dict(size="medium"))
        self.registry.add_item("general", "saucer", dict(size="medium"))
        self.registry.add_item("specific", "spoon", dict(size="medium"))

        cup = Item("general", "cup", dict(size="medium"))
        saucer = Item("general", "saucer", dict(size="medium"))
        spoon = Item("specific", "spoon", dict(size="medium"))

        self.assertTrue(cup in self.registry.all_items("general"))
        self.assertTrue(saucer in self.registry.all_items("general"))
        self.assertEquals([spoon], self.registry.all_items("specific"))
