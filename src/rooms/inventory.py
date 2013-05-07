
from rooms.item_registry import ItemRegistry

_registry = ItemRegistry()

def set_registry(registry):
    global _registry
    _registry = registry

def register_item(item):
    _registry.add_item(item)

def lookup(item_type):
    return _registry.get_item(item_type)


class Item(dict):
    def __init__(self, item_type, category="", price=0.0, **state):
        super(Item, self).__init__()
        self.item_type = item_type
        self.category = category
        self.price = price
        self.update(state)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            return None

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def has_properties(self, properties):
        return all([item in self.items() for item in properties.items()])

    def external(self):
        return self.copy()


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

    def get_amount(self, item_type):
        return self._items[item_type]

    def all_items(self):
        return self._items

    def find_items(self, **kwargs):
        return [(lookup(item), amount) for (item, amount) in \
            self._items.items() if lookup(item).has_properties(kwargs)]

    def external(self, **kwargs):
        return [(item.external(), amount) for (item, amount) in \
            self.find_items(**kwargs)]

    def get_item(self, item_type):
        amount = self.get_amount(item_type)
        if amount:
            return lookup(item_type), amount
        else:
            raise Exception("No items of type %s" % item_type)
