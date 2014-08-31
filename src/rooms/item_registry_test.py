
import unittest

from rooms.item_registry import ItemRegistry
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
