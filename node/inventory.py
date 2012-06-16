
class Item(dict):
    def __getattr__(self, name):
        return self.__getitem__(name)

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

def create_item(**kwargs):
    item = Item()
    for key, value in kwargs.items():
        item[key] = value
    return item


class Inventory:
    def __init__(self):
        self._items = []

    def add_item(self, item):
        self._items.append(item)

    def all_items(self):
        return self._items
