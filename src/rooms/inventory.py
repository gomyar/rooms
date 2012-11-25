

class ItemRegistry(object):
    def __init__(self):
        self._registered = dict()

    def lookup(self, item_type):
        return self._registered[item_type]

    def add_item(self, item):
        self._registered[item.item_type] = item


_registry = ItemRegistry()

def register_item(item):
    _registry.add_item(item)

def lookup(item_type):
    return _registry.lookup(item_type)


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


class Inventory(object):
    def __init__(self):
        self._items = dict()

    def __iter__(self):
        for item_type in self._items.keys():
            yield item_type

    def add_item(self, item_type, count=1):
        if item_type not in self._items:
            self._items[item_type] = 0
        self._items[item_type] += count

    def remove_item(self, item_type, count=1):
        if item_type in self._items:
            self._items[item_type] -= count
            if self._items[item_type] <= 0:
                self._items.pop(item_type)

    def all_items(self):
        return self._items

    def find_items(self, **kwargs):
        return [lookup(item) for item in self._items.keys() if \
            lookup(item).has_properties(kwargs)]

    def external(self):
        return self._items
