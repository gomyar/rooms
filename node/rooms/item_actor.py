
from actor import Actor


class ItemActor(Actor):
    def pick_up(self, this, player):
        player.inventory.add_item(self)
        self.remove()

    def inventory_item(self):
        return None
