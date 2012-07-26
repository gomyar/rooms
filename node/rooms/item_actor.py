
from actor import Actor
from actor import expose


class ItemActor(Actor):
    @expose()
    def pick_up(self, this, player):
        player.inventory.add_item(self)
        self.remove()
