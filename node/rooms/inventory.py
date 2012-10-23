
from rooms.item_actor import ItemActor


class Item(dict):
    def __init__(self, item_type):
        super(Item, self).__init__()
        self.item_type = item_type

    def __getattr__(self, name):
        return self.__getitem__(name)

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def has_properties(self, properties):
        return all([item in self.items() for item in properties.items()])


def create_item(item_type, **kwargs):
    item = Item(item_type)
    for key, value in kwargs.items():
        item[key] = value
    return item


class Inventory:
    def __init__(self):
        self._items = dict()

    def add_item(self, item_type, count=1):
        if item_type.item_type not in self._items:
            self._items[item_type.item_type] = 0
        self._items[item_type.item_type] += count

    def all_items(self):
        return self._items

    def find_items(self, **kwargs):
        return [item for item in self._items.keys() if item.has_properties(kwargs)]
