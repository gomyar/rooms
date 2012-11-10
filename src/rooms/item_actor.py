
from actor import Actor


class ItemActor(Actor):
    def __init__(self, actor_id, item_type):
        super(ItemActor, self).__init__(actor_id)
        self.item_type = item_type