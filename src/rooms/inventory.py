

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

    def total(self):
        return sum(self._items.values())

    def all_items(self):
        return self._items.copy()

    def items(self):
        return self._items.items()

    def keys(self):
        return self._items.keys()

    def get_item(self, item_type):
        amount = self.get_amount(item_type)
        if amount:
            return lookup(item_type), amount
        else:
            raise Exception("No items of type %s" % item_type)
