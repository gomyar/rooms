
import json
import os

import logging
log = logging.getLogger("rooms.item_registry")


def _create_items(data):
    items = dict()
    for cat, itemdict in data.items():
        items[cat] = items.get(cat, {})
        for item_type, itemdata in itemdict.items():
            items[cat][item_type] = Item(cat, item_type, itemdata)
    return items


class ItemRegistry(object):
    def __init__(self):
        self.categories = dict()

    def get_item(self, category, item_type):
        return self.categories.get(category, {}).get(item_type)

    def items_by_category(self, category, **filters):
        return filter(
            lambda item: all(ff in item.data.items() for ff in filters.items()),
            self.categories.get(category, {}).values())

    def get_categories(self):
        return self.categories.keys()

    def load_from_json(self, json_str):
        categories = _create_items(json.loads(json_str))
        self.categories.update(categories)

    def load_from_directory(self, directory_path):
        for filename in os.listdir(os.path.join(directory_path, "items")):
            if filename.endswith(".json"):
                log.info("Loading items from %s", filename)
                filepath = os.path.join(directory_path, "items", filename)
                self.load_from_json(open(filepath).read())


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
