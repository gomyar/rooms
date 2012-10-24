
from actor import Actor


class ItemActor(Actor):
    def __init__(self, actor_id, item_type):
        super(ItemActor, self).__init__(actor_id)
        self.item_type = item_type

    def pick_up(self, this, player):
        player.inventory.add_item(self)
        self.remove()

    def inventory_item(self):
        return None
