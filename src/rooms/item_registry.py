

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


class ItemRegistry(object):
    def __init__(self):
        self._items = dict()

    def add_item(self, item):
        self._items[item.item_type] = item

    def get_item(self, item_type):
        return self._items[item_type]

    def items(self, category=""):
        return [item for item in self._items.values() if \
            (not category or item.category == category)]
