
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
