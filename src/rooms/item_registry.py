

class ItemRegistry(object):
    def __init__(self, container):
        self._container = container

    def save_item(self, category, item_type, data):
        self._container.save_item(Item(category, item_type, data))

    def get_item(self, category, item_type):
        return self._container.load_item(category, item_type)

    def items_by_category(self, category):
        return self._container.load_items_by_category(category)

    def all_items(self):
        return self._container.all_items()


class Item(object):
    def __init__(self, category, item_type, data=None):
        self.category = category
        self.item_type = item_type
        self.data = data or {}

    def __eq__(self, rhs):
        return rhs and isinstance(rhs, Item) and \
            self.category == rhs.category and \
            self.item_type == rhs.item_type and self.data == rhs.data

    def __repr__(self):
        return "<Item %s %s>" % (self.category, self.item_type)
