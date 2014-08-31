

class ItemRegistry(object):
    _instance = None

    def __init__(self, container):
        self._container = container

    def add_item(self, category, item_type, data):
        self._container.save_item(Item(category, item_type, data))


class Item(object):
    def __init__(self, category, item_type, data=None):
        self.category = category
        self.item_type = item_type
        self.data = data or {}
